from aiogram import Bot, Dispatcher, html
from aiogram.filters import CommandStart
from aiogram.filters import Command
from aiogram.types import Message
dp = Dispatcher()

from states import cancel
# Отдельно импортируем отмену в первую очередь

from states import *
# Импортируем все остальные команды, чтобы бот их обрабатывал

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.reply(f"Здравствуйте, {html.bold(message.from_user.full_name)}!")

@dp.message(Command("end"))
async def echo_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message obj (like a text, photo, sticker etc.)
    """
    try:
        # Send a copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the obj is supported to be copied so need to handle it
        await message.answer("Nice try!")
