import logging

import aiogram.exceptions
from aiogram import F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import *
from aiogram.methods import edit_message_text
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from db_manager.main import *
from handle_functions.dp import dp

from sqlalchemy.exc import NoResultFound

from handle_functions.manage_flashcards import ManageState


class EditCardCallback(CallbackData, prefix="EditFlashcard"):
    state: str
    mode: str

class EditFlashcard(StatesGroup):
    id = State()
    editing = State()
    title = State()
    category = State()
    question = State()
    answer = State()

    markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Заголовок", callback_data=EditCardCallback(state="edit", mode="title").pack()),
                InlineKeyboardButton(text="Категория", callback_data=EditCardCallback(state="edit", mode="category").pack())
            ],
            [
                InlineKeyboardButton(text="Вопрос", callback_data=EditCardCallback(state="edit", mode="question").pack()),
                InlineKeyboardButton(text="Ответ", callback_data=EditCardCallback(state="edit", mode="answer").pack())
            ],
            [
                InlineKeyboardButton(text="Завершить изменение", callback_data=EditCardCallback(state="edit", mode="end").pack())
            ]
    ])

@dp.message(EditFlashcard.id)
async def select_flashcard(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        user = data.get("user")
        card_id: int = int(message.text)
        flashcard = get_flashcard_local_user(card_id, user)
        if flashcard is None:
            await message.answer("Такой карты не существует!")
            await state.clear()
            return
        await state.set_state(EditFlashcard.editing)
        await state.update_data(flashcard=flashcard)
        await message.answer(
            flashcard.format() + "\nВыберите, что вы хотите изменить",
            reply_markup=EditFlashcard.markup)
    except ValueError as e:
        logging.error(f"Failed to cast into int: {e}")
        await message.answer(
            "Некорректный формат ввода числа. Попробуйте снова.",
            reply_markup=ReplyKeyboardRemove()
        )
    except RuntimeError as e:
        await state.clear()
        logging.error(f"Failed to retrieve flashcard from db: {e}, ")
        await message.answer(f"Что-то пошло не так! Не удалось получить флеш-карту для изменения.")

@dp.callback_query(EditCardCallback.filter(F.state == "edit"))
async def edit_menu(query: CallbackQuery, callback_data: EditCardCallback, state: FSMContext):
    data = await state.get_data()
    if 'flashcard' in data:
        flashcard: Flashcard = data["flashcard"]
    else:
        await query.answer("Это сообщение старое и больше не работает.")
        await query.message.delete()
        return

    edit_text = ""
    match callback_data.mode:
        case "title":
            await query.answer("Выбрано изменение заголовка")
            if query.message.text == "Выбрано изменение заголовка. Введите новый заголовок":
                return
            await state.set_state(EditFlashcard.title)
            edit_text = "Выбрано изменение заголовка. Введите новый заголовок"
        case "category":
            await query.answer("Выбрано изменение категории")
            if query.message.text == "Выбрано изменение категории. Введите новое название категории":
                return
            await state.set_state(EditFlashcard.category)
            edit_text += "Выбрано изменение категории. Введите новое название категории"
        case "question":
            await query.answer("Выбрано изменение вопроса")
            if query.message.text == "Выбрано изменение вопроса. Введите новый вопрос":
                return
            await state.set_state(EditFlashcard.question)
            edit_text += "Выбрано изменение вопроса. Введите новый вопрос"
        case "answer":
            await query.answer("Выбрано изменение ответа")
            if query.message.text == "Выбрано изменение ответа. Введите новый ответ":
                return
            await state.set_state(EditFlashcard.answer)
            edit_text += "Выбрано изменение ответа. Введите новый ответ"
        case "end":
            await query.answer("Завершение изменения")
            await query.message.edit_text("Сохранение изменений", reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))
            try:
                update()
                await query.message.edit_text("Карта успешно сохранена")
            except Exception as e:
                logging.error(f"Couldn't save flashcard: {e}")

            if data.get("from_menu", False):
                from handle_functions.manage_flashcards import select_card_callback
                await state.set_state(ManageState.card_menu)
                await select_card_callback(query, data.get("callback_data"), state)
            else:
                await state.clear()
        case _:
            await query.answer("Выберите, что изменить")
            edit_text += "Выберите какой параметр карты изменить"

    if edit_text != "":
        if query.message.text == flashcard.format() + "\n" + edit_text:
            return
        await query.message.edit_text(flashcard.format() + "\n" + edit_text, reply_markup=EditFlashcard.markup)
        await state.update_data(
            chat_id=query.message.chat.id,
            message_id=query.message.message_id,
            extra_text=edit_text,
            bot=query.bot
        )

@dp.message(EditFlashcard.title)
async def edit_parameter(message: Message, state: FSMContext):
    await message.delete()
    data = await state.get_data()
    flashcard: Flashcard = data["flashcard"]
    flashcard.title = message.text
    await state.update_data(flashcard=flashcard)
    try:
        await edit_message_text.EditMessageText(
            text=flashcard.format() + "\n" + data["extra_text"],
            chat_id=data["chat_id"],
            message_id=data["message_id"],
            reply_markup=EditFlashcard.markup
        ).as_(data["bot"])
    except aiogram.exceptions.TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        await message.answer("Что-то пошло не так! Не удалось изменить параметр")
        logging.error(e)

@dp.message(EditFlashcard.category)
async def edit_parameter(message: Message, state: FSMContext):
    await message.delete()
    data = await state.get_data()
    flashcard: Flashcard = data["flashcard"]
    category_name = "Без категории" if message.text == "." else message.text
    categories = get_categories(user_id=flashcard.user_id)
    category = None
    for c in categories:
        if c.name == category_name:
            category = c
            break
    if category is None:
        category = Category(name=category_name, user=flashcard.user, user_id=flashcard.user_id)
        add(category)
    flashcard.category = category
    flashcard.category_id = category.id
    await state.update_data(flashcard=flashcard)
    try:
        await edit_message_text.EditMessageText(
            text=flashcard.format() + "\n" + data["extra_text"],
            chat_id=data["chat_id"],
            message_id=data["message_id"],
            reply_markup=EditFlashcard.markup
        ).as_(data["bot"])
    except aiogram.exceptions.TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        await message.answer("Что-то пошло не так! Не удалось изменить параметр")
        logging.error(e)

@dp.message(EditFlashcard.question)
async def edit_parameter(message: Message, state: FSMContext):
    await message.delete()
    data = await state.get_data()
    flashcard: Flashcard = data["flashcard"]
    flashcard.question = message.text
    await state.update_data(flashcard=flashcard)
    try:
        await edit_message_text.EditMessageText(
            text=flashcard.format() + "\n" + data["extra_text"],
            chat_id=data["chat_id"],
            message_id=data["message_id"],
            reply_markup=EditFlashcard.markup
        ).as_(data["bot"])
    except aiogram.exceptions.TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        await message.answer("Что-то пошло не так! Не удалось изменить параметр")
        logging.error(e)

@dp.message(EditFlashcard.answer)
async def edit_parameter(message: Message, state: FSMContext):
    await message.delete()
    data = await state.get_data()
    flashcard: Flashcard = data["flashcard"]
    flashcard.answer = message.text
    await state.update_data(flashcard=flashcard)
    try:
        await edit_message_text.EditMessageText(
            text=flashcard.format() + "\n" + data["extra_text"],
            chat_id=data["chat_id"],
            message_id=data["message_id"],
            reply_markup=EditFlashcard.markup
        ).as_(data["bot"])
    except aiogram.exceptions.TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        await message.answer("Что-то пошло не так! Не удалось изменить параметр")
        logging.error(e)
