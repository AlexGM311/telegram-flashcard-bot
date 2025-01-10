import asyncio

from aiogram import Bot

from db_manager.main import *
from db_manager.models import *

async def check_reviews(bot: Bot, minutes: int):
    while True:
        if not 9 > datetime.now().hour > 23:
            for review in get_all_due():
                user = review.user
                await bot.send_message(
                    chat_id=user.chat_id,
                    text="У вас есть карты, которые можно проверить! Введите команду /review чтобы проверить себя.",
                )
        await asyncio.sleep(minutes)