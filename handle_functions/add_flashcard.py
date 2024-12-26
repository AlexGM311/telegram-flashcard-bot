import logging

from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import *
from aiogram.methods import edit_message_text
from aiogram.types import Message, ReplyKeyboardRemove

import db_manager
from handlers import dp
from helper_classes import Flashcard, error_types, User


class AddFlashcard(StatesGroup):
    title = State()
    category = State()
    question = State()
    answer = State()

@dp.message(Command("add_flashcard"))
async def add_flashcard_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(AddFlashcard.title)
    flashcard: Flashcard = Flashcard()
    flashcard.user_id = message.from_user.id
    text = f"Флеш-карта на данный момент: \n{flashcard.format()}\n"
    msg: Message = await message.answer(
        text + "Выберите заголовок для карточки. Введите точку, если хотите, чтобы название совпадало с вопросом на карточке."
    )
    await state.update_data(
        user=User(user_telegram_id=message.from_user.id, chat_id=message.chat.id),
        message_id=msg.message_id,
        bot=msg.bot,
        flashcard=flashcard
    )

@dp.message(AddFlashcard.title)
async def process_title(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    flashcard: Flashcard = data["flashcard"]
    flashcard.title = "-" if message.text == "." else message.text
    text = f"Флеш-карта на данный момент: \n{flashcard.format()}\n"
    user: User = data["user"]
    await edit_message_text.EditMessageText(
        text=text + "Введите название категории для карточки или отправьте точку, если без категории.",
        message_id=data["message_id"],
        chat_id=user.chat_id
    ).as_(data["bot"])
    await state.set_state(AddFlashcard.category)
    await message.delete()
    await state.update_data(flashcard=flashcard)

@dp.message(AddFlashcard.category)
async def process_category(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    flashcard: Flashcard = data["flashcard"]
    flashcard.category = "Без категории" if message.text == "." else message.text
    text = f"Флеш-карта на данный момент: \n{flashcard.format()}\n"
    user: User = data["user"]
    await edit_message_text.EditMessageText(
        text=text + "Введите вопрос своей карточки",
        message_id=data["message_id"],
        chat_id=user.chat_id
    ).as_(data["bot"])
    await state.set_state(AddFlashcard.question)
    await message.delete()
    await state.update_data(flashcard=flashcard)

@dp.message(AddFlashcard.question)
async def process_question(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    flashcard: Flashcard = data["flashcard"]
    flashcard.question = message.text
    flashcard.title = message.text if flashcard.title == "-" else flashcard.title
    text = f"Флеш-карта на данный момент: \n{flashcard.format()}\n"
    user: User = data["user"]
    await edit_message_text.EditMessageText(
        text=text + "Введите ответ на вопрос",
        message_id=data["message_id"],
        chat_id=user.chat_id
    ).as_(data["bot"])
    await state.set_state(AddFlashcard.answer)
    await message.delete()
    await state.update_data(flashcard=flashcard)

@dp.message(AddFlashcard.answer)
async def process_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    flashcard: Flashcard = data["flashcard"]
    flashcard.answer = message.text
    text = f"Флеш-карта на данный момент: \n{flashcard.format()}\n"
    user: User = data["user"]
    await edit_message_text.EditMessageText(
        text=text + "Сохранение...",
        message_id=data["message_id"],
        chat_id=user.chat_id
    ).as_(data["bot"])
    try:
        flashcard_id = db_manager.add_flashcard(flashcard)
        await message.answer(
            f"Карта успешно создана. Её идентификатор - {flashcard_id}.",
            reply_markup=ReplyKeyboardRemove()
        )
    except error_types.MissingEntryError:
        user: User = data["user"]
        db_manager.add_user(user.telegram_id, user.chat_id)
        flashcard_id = db_manager.add_flashcard(flashcard)
        await message.answer(
            f"Карта успешно создана. Её идентификатор - {flashcard_id}.",
            reply_markup=ReplyKeyboardRemove()
        )
    except error_types.DatabaseError as e:
        await message.answer(
            "Что-то пошло не так! Карту не удалось создать.",
            reply_markup=ReplyKeyboardRemove()
        )
        logging.error(str(e) + "; Couldn't save user flashcard: " + str(flashcard))

    await state.clear()
    await message.delete()
    await state.update_data(flashcard=flashcard)
