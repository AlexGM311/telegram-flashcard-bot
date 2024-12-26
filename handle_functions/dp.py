from aiogram import Dispatcher
dp: Dispatcher | None = None

def set_dp(dp_new: Dispatcher):
    global dp
    dp = dp_new
