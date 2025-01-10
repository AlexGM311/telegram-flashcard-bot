import logging

from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import *
from aiogram.methods import edit_message_text
from aiogram.types import Message, ReplyKeyboardRemove

from sqlalchemy.exc import NoResultFound
from db_manager.main import *
from db_manager.models import *
from handlers import dp


class AddFlashcard(StatesGroup):
    title = State()
    category = State()
    question = State()
    answer = State()

@dp.message(Command("add_flashcard"))
async def add_flashcard_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(AddFlashcard.title)
    try:
        user = get_user(message.from_user.id)
    except NoResultFound:
        user = User(id=message.from_user.id, chat_id=message.chat.id)
        add(user)
    flashcard: Flashcard = Flashcard(user=user)
    text = f"Флеш-карта на данный момент: \n{flashcard.format()}\n"
    msg: Message = await message.answer(
        text + "Выберите заголовок для карточки. Введите точку, если хотите, чтобы название совпадало с вопросом на карточке."
    )
    await state.update_data(
        user=user,
        message_id=msg.message_id,
        bot=msg.bot,
        flashcard=flashcard,
        from_menu = False
    )

@dp.message(AddFlashcard.title)
async def process_title(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    flashcard: Flashcard = data.get("flashcard")
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
    flashcard: Flashcard = data.get("flashcard")
    user: User = data.get("user")
    category_name = "Без категории" if message.text == "." else message.text
    categories = get_categories(user_id=user.id, name=category_name)
    if len(categories) == 0:
        category = Category(name=category_name, user_id=user.id)
    else:
        category = categories[0]
    flashcard.category = category
    flashcard.category_id = category.id
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
        if len(user.flashcards) != 0:
            if user.flashcards[-1].local_id:
                flashcard.local_id = user.flashcards[-1].local_id + 1
            else:
                flashcard.local_id = len(user.flashcards)
        else:
            flashcard.local_id = 1
        add(flashcard)
        await message.answer(
            f"Карта успешно создана. Её идентификатор - {flashcard.local_id}.",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        await message.answer("Что-то пошло не так!")
        logging.error(e)

    await state.clear()
    await message.delete()
    await state.update_data(flashcard=flashcard)
