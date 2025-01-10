import asyncio
import logging

from aiogram import Bot

from db_manager.main import *
from db_manager.models import *

async def check_reviews(bot: Bot, minutes: int):
    while True:
        t = datetime.now()
        if t.hour == 19 and t.minute == 0:
            users: set[User] = set()
            for review in get_all_due():
                users.add(review.user)
            for user in users:
                await bot.send_message(
                    chat_id=user.chat_id,
                    text="У вас есть карты, которые можно проверить! Введите команду /review чтобы проверить себя.",
                )
        now = datetime.now()
        today_1900 = now.replace(hour=19, minute=0, second=0, microsecond=0)

        if now < today_1900:
            next_1900 = today_1900
        else:
            next_1900 = today_1900 + timedelta(days=1)

        time_remaining = next_1900 - now

        logging.info(f"Waiting for {time_remaining.total_seconds()} seconds until next card")
        await asyncio.sleep(time_remaining.total_seconds())
