import logging

from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import *
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

import db_manager
from handlers import dp
from helper_classes import Flashcard

class EditFlashcard(StatesGroup):
    id = State()

@dp.message(Command("e"))
async def edit_flashcard_handler(message: Message, state: FSMContext):
    await state.set_state(EditFlashcard.id)
    await message.answer(
        "Введите идентификатор изменяемой карточки",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Тест", callback_data="Test")],
            [InlineKeyboardButton(text="Тест1", callback_data="Test1"), InlineKeyboardButton(text="Тест2", callback_data="Test2")]])
    )


@dp.message(EditFlashcard.id)
async def select_flashcard(message: Message, state: FSMContext):
    try:
        card_id: int = int(message.text)
        flashcard: Flashcard = db_manager.get_flashcard(card_id)

    except ValueError as e:
        logging.error(f"Failed to cast into int: {e}")
        await message.answer(
            "Некорректный формат ввода числа. Попробуйте снова.",
            reply_markup=ReplyKeyboardRemove()
        )
    except RuntimeError as e:
        logging.error(f"Failed to retrieve flashcard from db: {e}, ")
        await message.answer(f"Что-то пошло не так! Не удалось получить флеш-карту для изменения.")
