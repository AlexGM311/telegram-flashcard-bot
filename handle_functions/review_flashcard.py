import logging

import jellyfish
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import *
from aiogram.types import Message, ReplyKeyboardRemove

import db_manager
import helper_classes.error_types
from handle_functions.dp import dp
from helper_classes import Flashcard


class ReviewFlashcard(StatesGroup):
    id = State()
    reviewing = State()

@dp.message(Command("review_flashcard"))
async def review_flashcard_handler(message: Message, state: FSMContext):
    await state.set_state(ReviewFlashcard.id)
    await message.answer(
        "Введите идентификатор повторяемой карточки",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(ReviewFlashcard.id)
async def select_flashcard(message: Message, state: FSMContext):
    try:
        card_id: int = int(message.text)
        flashcard: Flashcard = db_manager.get_flashcard(card_id)
        await state.set_state(ReviewFlashcard.reviewing)
        await state.update_data(flashcard=flashcard)
        await message.answer(
            "Введите ответ на вопрос: \n" + flashcard.question)
    except ValueError as e:
        logging.error(f"Failed to cast into int: {e}")
        await message.answer(
            "Некорректный формат ввода числа. Попробуйте снова.")
    except helper_classes.error_types.MissingEntryError as e:
        await state.clear()
        logging.error(f"Failed to retrieve flashcard from db: {e}, ")
        await message.answer(f"Карты с таким номером не существует.")

@dp.message(ReviewFlashcard.reviewing)
async def handle_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    answer = message.text
    card: Flashcard = data["flashcard"]
    correct = card.answer
    dist = jellyfish.damerau_levenshtein_distance(answer, correct)
    if dist == 0:
        await message.answer(
            "Правильно!"
        )
        db_manager.record_answer(card.card_id, card.user_id, True)
    elif dist <= 2:
        await message.answer(
            "Почти! Правильный ответ: " + correct
        )
        db_manager.record_answer(card.card_id, card.user_id, True)
    else:
        await message.answer(
            "Неверно! Правильный ответ: " + correct
        )
        db_manager.record_answer(card.card_id, card.user_id, False)
    await state.clear()
