import logging

from aiogram import html, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from handle_functions.dp import dp


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.reply(f"Здравствуйте, {html.bold(message.from_user.full_name)}!")

@dp.message(Command("cancel"))
@dp.message(F.text.casefold() == "cancel")
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

from handle_functions import add_flashcard, edit_flashcard, delete_flashcard, review_flashcard
