from aiogram import F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from handle_functions.dp import dp
from db_manager.main import *
from db_manager.models import *

class CbQuery(CallbackData, prefix="notif"):
    change: bool

class NotifState(StatesGroup):
    main = State()
    turn_on = InlineKeyboardButton(text="**Включить** уведомления", callback_data=CbQuery(change=True).pack())
    turn_off = InlineKeyboardButton(text="**Выключить** уведомления", callback_data=CbQuery(change=True).pack())

@safe_callback_handler
@dp.message(Command("notifications"))
async def handle_notifications(message: Message, state: FSMContext):
    user: User = get_user(message.from_user.id)
    if user is None:
        user = User(id=message.from_user.id, chat_id=message.chat.id)
        add(user)
    if user.notify:
        msg = await message.answer("Ваши уведомления включены. Нажмите кнопку, чтобы выключить.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[NotifState.turn_off]]))
    else:
        msg = await message.answer("Ваши уведомления выключены. Нажмите кнопку, чтобы включить.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[NotifState.turn_on]]))

@safe_callback_handler
@dp.callback_query(CbQuery.filter(F.change == True))
async def notif_callback(query: CallbackQuery, callback_data: CallbackData, state: FSMContext):
    await query.answer("Настройки уведомлений изменены")
    user: User = get_user(query.from_user.id)
    user.notify = not user.notify
    update()
    if user.notify:
        msg = await query.message.edit_text("Ваши уведомления включены. Нажмите кнопку, чтобы выключить.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[NotifState.turn_off]]))
    else:
        msg = await query.message.edit_text("Ваши уведомления выключены. Нажмите кнопку, чтобы включить.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[NotifState.turn_on]]))
