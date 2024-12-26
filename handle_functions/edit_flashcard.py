import logging

from aiogram import F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import *
from aiogram.methods import edit_message_text
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

import db_manager
from handle_functions.dp import dp
from helper_classes import Flashcard


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

@dp.message(Command("edit_flashcard"))
async def edit_flashcard_handler(message: Message, state: FSMContext):
    await state.set_state(EditFlashcard.id)
    await message.answer(
        "Введите идентификатор изменяемой карточки",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(EditFlashcard.id)
async def select_flashcard(message: Message, state: FSMContext):
    try:
        card_id: int = int(message.text)
        user = db_manager.get_user_telegram_id(message.from_user.id)
        logging.info(str(user) + str(card_id))
        flashcard: Flashcard = db_manager.get_flashcard_local_user(card_id, user['id'])
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
async def edit_title(query: CallbackQuery, callback_data: EditCardCallback, state: FSMContext):
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
                db_manager.update_flashcard(data["flashcard"])
                await query.message.edit_text("Карта успешно сохранена")
            except RuntimeError as e:
                logging.error(f"Couldn't save flashcard: {e}")
            await state.clear()

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
    card: Flashcard = data["flashcard"]
    card.title = message.text
    await state.update_data(flashcard=card)
    await edit_message_text.EditMessageText(
        text=card.format() + "\n" + data["extra_text"],
        chat_id=data["chat_id"],
        message_id=data["message_id"],
        reply_markup=EditFlashcard.markup
    ).as_(data["bot"])

@dp.message(EditFlashcard.category)
async def edit_parameter(message: Message, state: FSMContext):
    await message.delete()
    data = await state.get_data()
    card: Flashcard = data["flashcard"]
    card.category = message.text
    await state.update_data(flashcard=card)
    await edit_message_text.EditMessageText(
        text=card.format() + "\n" + data["extra_text"],
        chat_id=data["chat_id"],
        message_id=data["message_id"],
        reply_markup=EditFlashcard.markup
    ).as_(data["bot"])

@dp.message(EditFlashcard.question)
async def edit_parameter(message: Message, state: FSMContext):
    await message.delete()
    data = await state.get_data()
    card: Flashcard = data["flashcard"]
    card.question = message.text
    await state.update_data(flashcard=card)
    await edit_message_text.EditMessageText(
        text=card.format() + "\n" + data["extra_text"],
        chat_id=data["chat_id"],
        message_id=data["message_id"],
        reply_markup=EditFlashcard.markup
    ).as_(data["bot"])

@dp.message(EditFlashcard.answer)
async def edit_parameter(message: Message, state: FSMContext):
    await message.delete()
    data = await state.get_data()
    card: Flashcard = data["flashcard"]
    card.answer = message.text
    await state.update_data(flashcard=card)
    await edit_message_text.EditMessageText(
        text=card.format() + "\n" + data["extra_text"],
        chat_id=data["chat_id"],
        message_id=data["message_id"],
        reply_markup=EditFlashcard.markup
    ).as_(data["bot"])
