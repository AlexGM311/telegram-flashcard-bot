import logging

from aiogram import html
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy.exc import NoResultFound

from db_manager.main import get_connection
from handle_functions.dp import dp


@dp.message(CommandStart())
async def command_start_handler(message: Message, command: CommandObject) -> None:
    payload = command.args

    if not payload:
        await message.reply(f"Здравствуйте, {html.bold(message.from_user.full_name)}!")
    else:
        from db_manager.main import get_flashcard_by_uuid, get_user, add
        from db_manager.models import User, FlashcardUser

        flashcard = get_flashcard_by_uuid(payload)

        if flashcard is None:
            await message.reply(
                f"Здравствуйте, {html.bold(message.from_user.full_name)}! Вы попытались добавить карту, которой не существует.")

        try:
            user = get_user(message.from_user.id)
        except NoResultFound:
            user = User(id=message.from_user.id, chat_id=message.chat.id)
            add(user)

        if user.id == flashcard.user_id:
            await message.reply("Нельзя добавить собсвтенную карту!")
            return

        fuser = get_connection(user.id, flashcard.id)
        if fuser is not None:
            await message.reply(f"У вас уже есть данная карта.")
            return
        fuser = FlashcardUser(user=user, flashcard=flashcard)
        add(fuser)
        await message.reply(f"Вы добавили карту '{flashcard.title}'!")

@dp.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        "Отменено.",
        reply_markup=ReplyKeyboardRemove()
    )


# noinspection PyUnresolvedReferences
from handle_functions import add_flashcard, edit_flashcard, delete_flashcard, review_flashcard, manage_flashcards
