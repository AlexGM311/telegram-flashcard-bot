import logging

from aiogram import F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.methods import SendChatAction, edit_message_media, delete_message
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, BufferedInputFile, \
    InputMediaPhoto
from sqlalchemy.exc import NoResultFound

from handle_functions.dp import dp, safe_callback_handler
from db_manager.main import *
from db_manager.models import *


from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

@safe_callback_handler
def create_image_with_wrapped_text(text, font_name: str, width=800, height=400, font_size=40, padding=20):

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype(font_name, font_size)
        print("Succesfully loaded the font")
    except IOError:
        print("Couldn't load font")
        font = ImageFont.load_default()

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = words[0]

        for word in words[1:]:
            test_line = f"{current_line} {word}"
            if draw.textlength(test_line, font=font) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        return lines

    text_width = width - 2 * padding
    lines = wrap_text(text, font, text_width)

    box = font.getbbox('A')
    line_height = (box[3] - box[1]) * 1.1
    text_block_height = line_height * len(lines)

    y = (height - text_block_height) // 2

    for line in lines:
        line_width = draw.textlength(line, font=font)
        x = (width - line_width) // 2
        draw.text((x, y), line, font=font, fill="black")
        y += line_height

    return image

@safe_callback_handler
def has_glyph(font: TTFont, glyph):
    for table in font['cmap'].tables:
        if ord(glyph) in table.cmap.keys():
            return True
    return False

@safe_callback_handler
def remove_control_characters(s):
    import unicodedata
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")

@safe_callback_handler
def determine_font(text):
    text = remove_control_characters(text)
    font_options = [
        'fonts/arial.ttf',
        'fonts/BIZ-UDGothicR.ttc',
        'fonts/msmincho.ttc',
    ]
    for font_name in font_options:
        font = TTFont(font_name, fontNumber=1)
        if all(has_glyph(font, c) for c in text):
            return font_name
    raise Exception(f'No suitable font for {text}.')


class ReviewCallback(CallbackData, prefix="Review"):
    index: int
    function: str

@safe_callback_handler
class ReviewFlashcard:
    button_row: list[list[InlineKeyboardButton]] = [[
        InlineKeyboardButton(text="Правильно", callback_data=ReviewCallback(index=5, function="difficulty").pack()),
        InlineKeyboardButton(text="Почти правильно",
                             callback_data=ReviewCallback(index=4, function="difficulty").pack()),
        InlineKeyboardButton(text="Не правильно", callback_data=ReviewCallback(index=2, function="difficulty").pack()),
    ]]
    flip = InlineKeyboardButton(text="Просмотреть правильный ответ",
                                callback_data=ReviewCallback(index=0, function="flip").pack())


@safe_callback_handler
@dp.message(Command("review"))
async def review_flashcard_handler(message: Message, state: FSMContext):
    user: User | None = None
    try:
        user = get_user(message.from_user.id)
    except NoResultFound:
        await message.answer("Вы ещё не создавали флеш-карт!")
        return

    due_cards = get_user_due_reviews(user)
    if len(due_cards) == 0:
        cards = list(user.flashcards) + [f.flashcard for f in user.shared_flashcards]
        if len(cards) == 0:
            await message.answer("У вас нет флеш-карт для повторения!")
            return
        worst_ease = -1

        flashcard = cards[0]
        for card in cards:
            review = get_user_card_review(user, card)
            if review is None or review.review_count == 0:
                flashcard = card
                break
            if worst_ease == -1 or worst_ease > review.ease_factor:
                flashcard = card
                worst_ease = review.ease_factor
        logging.info(worst_ease)
    else:
        flashcard = due_cards[0].flashcard
    await state.update_data(user=user, flashcard=flashcard, chat_id=message.chat.id,
                            bot=message.bot, from_menu=False)

    await display_question(message, state)


@safe_callback_handler
async def display_question(message: Message, state: FSMContext, edit_message: bool = False):
    import io
    data = await state.get_data()
    await SendChatAction(action="upload_photo", chat_id=data.get("chat_id")).as_(data.get("bot"))
    image = create_image_with_wrapped_text(data.get("flashcard").question, determine_font(data.get("flashcard").question))
    byte_arr = io.BytesIO()
    image.save(byte_arr, format='PNG')
    byte_arr.seek(0)

    if not edit_message:
        msg: Message = await data.get("bot").send_photo(data.get("chat_id"), BufferedInputFile(byte_arr.read(), "question.png"),
                                                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[ReviewFlashcard.flip]]))
        await state.update_data(message_id=msg.message_id)
    else:
        msg = message
        await message.edit_media(media=InputMediaPhoto(media=BufferedInputFile(byte_arr.read(), "question.png")),
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[[ReviewFlashcard.flip]]))
    await state.update_data(message_id=msg.message_id)

@safe_callback_handler
@dp.callback_query(ReviewCallback.filter(F.function == "flip"))
async def flip_card(query: CallbackQuery, callback_data: ReviewCallback, state: FSMContext):
    st = await state.get_state()
    data = await state.get_data()

    if not data.get("flashcard"):
        await query.answer("Это сообщение старое и больше не работает.")
        await query.message.delete()
        return

    import io

    await SendChatAction(action="upload_photo", chat_id=data.get("chat_id")).as_(data.get("bot"))
    image = create_image_with_wrapped_text(data.get("flashcard").answer, determine_font(data.get("flashcard").answer))
    byte_arr = io.BytesIO()
    image.save(byte_arr, format='PNG')
    byte_arr.seek(0)

    await edit_message_media.EditMessageMedia(
        media=InputMediaPhoto(media=BufferedInputFile(byte_arr.read(), "question.png")),
        message_id=data.get("message_id"),
        chat_id=data.get("chat_id"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=ReviewFlashcard.button_row)
    ).as_(data.get("bot"))

@safe_callback_handler
@dp.callback_query(ReviewCallback.filter(F.function == "difficulty"))
async def difficulty_callback(query: CallbackQuery, callback_data: ReviewCallback, state: FSMContext):
    st = await state.get_state()
    data = await state.get_data()

    if not data.get("flashcard"):
        await query.answer("Это сообщение старое и больше не работает.")
        await query.message.delete()
        return

    review = get_flashcard_user_review(data.get("user"), data.get("flashcard"))
    if review is None:
        review = CardReview(flashcard_id=data.get("flashcard").id, user_id=data.get("user").id, ease_factor=1)
        add(review)

    review.update_review(callback_data.index)
    update()
    if data.get("from_menu", False):
        from handle_functions.manage_flashcards import ManageState, reset_menu
        await state.set_state(ManageState.general)
        await reset_menu(query.message, state)
        await delete_message.DeleteMessage(
            chat_id=data.get("chat_id"),
            message_id=data.get("message_id")
        ).as_(data.get("bot"))
    else:
        await delete_message.DeleteMessage(
            chat_id=data.get("chat_id"),
            message_id=data.get("message_id")
        ).as_(data.get("bot"))
        await state.clear()
