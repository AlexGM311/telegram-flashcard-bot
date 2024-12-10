from typing import Dict

from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import *
from aiogram.types import Message, ReplyKeyboardRemove
from handlers import dp


class AddFlashcard(StatesGroup):
    title = State()
    category = State()
    question = State()
    answer = State()

@dp.message(Command("add_flashcard"))
async def add_flashcard_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(AddFlashcard.title)
    await message.answer(
        "Выберите заголовок для новой карточки. Введите точку, если хотите, чтобы название совпадало с вопросом на карточке.",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(AddFlashcard.title)
async def process_title(message: Message, state: FSMContext) -> None:
    data = await state.update_data(title=(message.text if message.text != '.' else "?"))
    await message.answer(
        f"Заголовок новой карточки: {data["title"]}.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AddFlashcard.category)
    await message.answer(
        "Введите категорию для карточки или отправьте точку, если без категории.",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(AddFlashcard.category)
async def process_category(message: Message, state: FSMContext) -> None:
    data = await state.update_data(category=(message.text if message.text != '.' else "Без категории"))
    await message.answer(
        f"Категория новой карточки: {data["category"]}",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AddFlashcard.question)
    await message.answer(
        f"Введите вопрос своей карточки",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(AddFlashcard.question)
async def process_question(message: Message, state: FSMContext) -> None:
    data = await state.update_data(question=message.text)
    await message.answer(
        f"Выбран вопрос: {message.text}" + ("" if data["title"] != "?" else "\nНазвание будет совпадать с вопросом.")
    )

async def add_to_db(message: Message, data: Dict[str, Any]):
    try:

