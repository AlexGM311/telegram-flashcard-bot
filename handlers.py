from aiogram import Bot, Dispatcher, html
from aiogram.filters import CommandStart
from aiogram.types import Message
dp = Dispatcher()

from states import cancel
# Отдельно импортируем отмену в первую очередь

from states import edit_flashcard, add_flashcard
# Импортируем все остальные команды, чтобы бот их обрабатывал

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.reply(f"Здравствуйте, {html.bold(message.from_user.full_name)}!")
