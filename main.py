import asyncio
import logging
from dotenv import load_dotenv
import os
import sys
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import db_manager

from aiogram import Dispatcher
dp = Dispatcher()

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

async def main() -> None:
    from handle_functions.dp import set_dp
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    db_manager.initialize_db()

    # And the run events dispatching
    set_dp(dp)
    import handlers
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
