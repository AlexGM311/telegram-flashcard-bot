import logging

from aiogram import F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import *
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.exc import NoResultFound

from handle_functions.dp import dp
from db_manager.main import *
from db_manager.models import *


class ManageCallback(CallbackData, prefix="Manage"):
    index: int
    function: str


class ManageState(StatesGroup):
    general = State()
    edit_card = State()
    function_row = [
        InlineKeyboardButton(text="◀", callback_data=ManageCallback(index=-1, function="back").pack()),
        InlineKeyboardButton(text="▲", callback_data=ManageCallback(index=-1, function="reduce").pack()),
        InlineKeyboardButton(text="▼", callback_data=ManageCallback(index=-1, function="expand").pack()),
        InlineKeyboardButton(text="▶", callback_data=ManageCallback(index=-1, function="forward").pack())
    ]
    card_menu = InlineKeyboardBuilder(
        [
            [
                InlineKeyboardButton(text="Изменить", callback_data=ManageCallback(index=0, function="edit").pack()),
                InlineKeyboardButton(text="Удалить", callback_data=ManageCallback(index=1, function="delete").pack()),
            ],
            [
                InlineKeyboardButton(text="Повторить", callback_data=ManageCallback(index=2, function="review").pack()),
                InlineKeyboardButton(text="Поделиться", callback_data=ManageCallback(index=3, function="share").pack())
            ],
            [
                InlineKeyboardButton(text="◀", callback_data=ManageCallback(index=4, function="return").pack())
            ]
        ])
    shared_card_menu = InlineKeyboardBuilder(
        [
            [
                InlineKeyboardButton(text="Удалить", callback_data=ManageCallback(index=0, function="delete").pack()),
                InlineKeyboardButton(text="Повторить", callback_data=ManageCallback(index=1, function="review").pack()),
            ],
            [
                InlineKeyboardButton(text="◀", callback_data=ManageCallback(index=4, function="return").pack())
            ]
        ])


def menu_builder(user: User, from_index: int, height: int, shared: bool) -> InlineKeyboardBuilder:
    if not shared:
        builder = InlineKeyboardBuilder()
        i = 0
        row: list[InlineKeyboardButton] = []
        while i < height * 2 and i + from_index < len(user.flashcards):
            row.append(InlineKeyboardButton(text=user.flashcards[i + from_index].title,
                                            callback_data=ManageCallback(index=i + from_index, function="card").pack()))
            if i % 2 == 1:
                builder.row(*row)
                row.clear()
            i += 1
        if len(row) == 1:
            row.append(InlineKeyboardButton(text=" ",
                                            callback_data=ManageCallback(index=i + from_index, function="filler").pack()))
            builder.row(*row)
            i += 1
            row.clear()
        row.clear()
        if from_index != 0:
            row.append(ManageState.function_row[0])
        if height > 1:
            row.append(ManageState.function_row[1])
        if height * 2 < len(user.flashcards):
            row.append(ManageState.function_row[2])
        if from_index < len(user.flashcards) - height * 2:
            row.append(ManageState.function_row[3])
        builder.row(*row)
        return builder

    builder = InlineKeyboardBuilder()
    i = 0
    row: list[InlineKeyboardButton] = []
    while i < height * 2 and i + from_index < len(user.shared_flashcards):
        row.append(InlineKeyboardButton(text=user.shared_flashcards[i + from_index].flashcard.title,
                                        callback_data=ManageCallback(index=i + from_index, function="card").pack()))
        if i % 2 == 1:
            builder.row(*row)
            row.clear()
        i += 1
    if len(row) == 1:
        row.append(InlineKeyboardButton(text=" ",
                                        callback_data=ManageCallback(index=i + from_index, function="filler").pack()))
        builder.row(*row)
        i += 1
        row.clear()
    row.clear()
    if from_index != 0:
        row.append(ManageState.function_row[0])
    if height > 1:
        row.append(ManageState.function_row[1])
    if height * 2 < len(user.shared_flashcards):
        row.append(ManageState.function_row[2])
    if from_index < len(user.shared_flashcards) - height * 2:
        row.append(ManageState.function_row[3])
    builder.row(*row)
    return builder

@dp.message(Command("manage"))
async def manage_handler(message: Message, state: FSMContext):
    user = None
    try:
        user = get_user(message.from_user.id)
    except NoResultFound:
        await message.answer("Вы ещё не создавали флеш-карт!")
        return
    if len(user.flashcards) == 0:
        await message.answer("У вас нет флеш-карт для изменения!")
        return
    await state.update_data(user=user)
    await state.update_data(shared=False)
    await state.set_state(ManageState.general)
    await reset_menu(message, state)

@dp.message(Command("manage_shared"))
async def manage_handler(message: Message, state: FSMContext):
    user = None
    try:
        user = get_user(message.from_user.id)
    except NoResultFound:
        await message.answer("С вами не делились флеш-картами!")
        return
    if len(user.shared_flashcards) == 0:
        await message.answer("С вами не делились флеш-картами!")
        return
    await state.update_data(user=user)
    await state.update_data(shared=True)
    await state.set_state(ManageState.general)
    await reset_menu(message, state)

async def reset_menu(message: Message, state: FSMContext, edit_message: bool = False):
    data = await state.get_data()
    user: User = data.get("user")
    height = 3
    builder = menu_builder(user, 0, height, data.get("shared"))
    if not edit_message:
        msg = await message.answer(
            "Ваш список карт:",
            reply_markup=builder.as_markup()
        )
        await state.update_data(message_id=msg.message_id, chat_id=msg.chat.id, bot=msg.bot)
    else:
        await message.edit_text(
            "Ваш список карт:",
            reply_markup=builder.as_markup()
        )
    await state.update_data(height=height, page=0, start_index=0)

@dp.callback_query(ManageCallback.filter(F.function == "forward"))
@dp.callback_query(ManageCallback.filter(F.function == "back"))
async def change_page(query: CallbackQuery, callback_data: ManageCallback, state: FSMContext):
    st = await state.get_state()
    if st is None:
        await query.answer("Это сообщение старое и больше не работает.")
        await query.message.delete()
        return

    data = await state.get_data()
    start_index: int = data.get("start_index")
    page = data.get("page")
    user: User = data.get("user")
    height: int = data.get("height")

    if callback_data.function == "back":
        start_index = max(0, start_index - 2 * height)
    else:
        start_index = min(len(user.flashcards) - height * 2, start_index + height * 2)

    builder = menu_builder(user, start_index, height, data.get("shared"))
    await state.update_data(start_index=start_index)
    try:
        await query.message.edit_text(
            "Ваш список карт:",
            reply_markup=builder.as_markup()
        )
        await query.answer("Страница переключена")
    except Exception as e:
        if "message is not modified" in str(e):
            await query.answer("Это первая страница!")
        else:
            await query.answer("Что-то пошло не так!")
            logging.error(e)


@dp.callback_query(ManageCallback.filter(F.function == "reduce"))
@dp.callback_query(ManageCallback.filter(F.function == "expand"))
async def resize_menu(query: CallbackQuery, callback_data: ManageCallback, state: FSMContext):
    st = await state.get_state()
    if st is None:
        await query.answer("Это сообщение старое и больше не работает.")
        await query.message.delete()
        return

    data = await state.get_data()
    user: User = data.get("user")
    height: int = data.get("height")
    start_index = data.get("start_index")

    if callback_data.function == "reduce":
        height = max(1, height - 1)
    else:
        height = min((len(user.flashcards) + 1) // 2, height + 1)

    builder = menu_builder(user, start_index, height, data.get("shared"))
    await state.update_data(height=height)
    try:
        await query.message.edit_text(
            "Ваш список карт:",
            reply_markup=builder.as_markup()
        )
        await query.answer("Высота изменена")
    except Exception as e:
        if "message is not modified" in str(e):
            await query.answer("Дальше изменить нельзя!!")
        else:
            await query.answer("Что-то пошло не так!")
            logging.error(e)


@dp.callback_query(ManageCallback.filter(F.function == "card"))
async def select_card_callback(query: CallbackQuery, callback_data: ManageCallback, state: FSMContext):
    st = await state.get_state()
    if st is None:
        await query.answer("Это сообщение старое и больше не работает.")
        await query.message.delete()
        return

    data = await state.get_data()
    await state.set_state(ManageState.edit_card)
    user: User = data.get("user")
    # noinspection PyTypeChecker
    flashcard: Flashcard = user.flashcards[callback_data.index] if not data.get("shared") else user.shared_flashcards[callback_data.index].flashcard
    await query.answer("Выбрано изменение карты")
    await state.update_data(flashcard=flashcard, callback_data=callback_data)
    await query.message.edit_text(
        f"Карта - {flashcard.title}\n(Вопрос - {flashcard.question})",
        reply_markup=(ManageState.card_menu.as_markup() if not data.get("shared") else ManageState.shared_card_menu.as_markup())
    )

async def select_card(state: FSMContext):
    from aiogram.methods import send_message, delete_message, edit_message_text
    st = await state.get_state()
    data = await state.get_data()
    if st is None:
        await send_message.SendMessage(
           text="Это сообщение старое и больше не работает.",
           chat_id=data.get("chat_id")
        )
        await delete_message.DeleteMessage(
            chat_id=data.get("chat_id"),
            message_id=data.get("message_id")
        )
        return

    await state.set_state(ManageState.edit_card)
    user: User = data.get("user")
    # noinspection PyTypeChecker
    flashcard: Flashcard = data.get("flashcard")
    await edit_message_text.EditMessageText(
        text=f"Карта - {flashcard.title}\n(Вопрос - {flashcard.question})",
        reply_markup=(
            ManageState.card_menu.as_markup() if not data.get("shared") else ManageState.shared_card_menu.as_markup()),
        message_id=data.get("message_id"),
        chat_id=data.get("chat_id")
    ).as_(data.get("bot"))
    await state.update_data(flashcard=flashcard)

@dp.callback_query(ManageCallback.filter(F.function == "return"))
async def return_to_menu(query: CallbackQuery, callback_data: ManageCallback, state: FSMContext):
    st = await state.get_state()
    if st is None:
        await query.answer("Это сообщение старое и больше не работает.")
        await query.message.delete()
        return

    data = await state.get_data()
    user: User = data.get("user")
    await state.set_state(ManageState.general)
    height: int = data.get("height")
    start_index: int = data.get("start_index")
    builder = menu_builder(user, start_index, height, data.get("shared"))
    await query.message.edit_text(
        "Ваш список карт:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(ManageCallback.filter(F.function == "edit"))
async def edit_card(query: CallbackQuery, callback_data: ManageCallback, state: FSMContext):
    st = await state.get_state()
    if st is None:
        await query.answer("Это сообщение старое и больше не работает.")
        await query.message.delete()
        return

    from handle_functions.edit_flashcard import EditFlashcard, edit_menu, EditCardCallback

    st = await state.get_state()
    if st is None:
        await query.answer("Это сообщение старое и больше не работает.")
        await query.message.delete()
        return

    await state.update_data(from_menu=True)
    await state.set_state(EditFlashcard.editing)
    await edit_menu(query, EditCardCallback(state="", mode=""), state)

@dp.callback_query(ManageCallback.filter(F.function == "delete"))
async def delete_card(query: CallbackQuery, callback_data: ManageCallback, state: FSMContext):
    st = await state.get_state()
    if st is None:
        await query.answer("Это сообщение старое и больше не работает.")
        await query.message.delete()
        return

    from handle_functions.delete_flashcard import delete_id

    st = await state.get_state()
    if st is None:
        await query.answer("Это сообщение старое и больше не работает.")
        await query.message.delete()
        return

    await state.update_data(from_menu=True)
    await delete_id(query.message, state, True)

@dp.callback_query(ManageCallback.filter(F.function == "review"))
async def review_card(query: CallbackQuery, callback_data: ManageCallback, state: FSMContext):
    st = await state.get_state()
    if st is None:
        await query.answer("Это сообщение старое и больше не работает.")
        await query.message.delete()
        return

    from handle_functions.review_flashcard import display_question
    await state.update_data(from_menu=True)
    await display_question(query.message, state, True)

@dp.callback_query(ManageCallback.filter(F.function == "share"))
async def share_card(query: CallbackQuery, callback_data: ManageCallback, state: FSMContext):
    st = await state.get_state()
    if st is None:
        await query.answer("Это сообщение старое и больше не работает.")
        await query.message.delete()
        return
    data = await state.get_data()
    flashcard: Flashcard = data.get("flashcard")

    await query.message.answer(f"Ссылка на флеш-карту: https://t.me/{'asev0_flashcard_bot'}?start={flashcard.uuid}")
    await query.answer("Успешно")
