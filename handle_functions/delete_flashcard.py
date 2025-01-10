import logging

from aiogram import F
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import *
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from handle_functions.dp import dp

from db_manager.main import *

class DeleteCardCallback(CallbackData, prefix="DeleteFlashcard"):
    delete: bool

class DeleteFlashcard(StatesGroup):
    id = State()

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Отменить удаление", callback_data=DeleteCardCallback(delete=False).pack()),
            InlineKeyboardButton(text="Удалить", callback_data=DeleteCardCallback(delete=True).pack())
         ]
    ])

async def delete_id(message: Message, state: FSMContext, edit_message: bool = False):
    data = await state.get_data()
    if not edit_message:
        await message.answer(
            f"Вы уверены, что хотите удалить флеш-карту:\n" + data.get("flashcard").format(),
            reply_markup=DeleteFlashcard.markup
        )
    else:
        await message.edit_text(
            f"Вы уверены, что хотите удалить флеш-карту:\n" + data.get("flashcard").format(),
            reply_markup=DeleteFlashcard.markup
        )

@dp.callback_query(DeleteCardCallback.filter(F.delete == True))
async def delete_flashcard(query: CallbackQuery, callback_data: DeleteCardCallback, state: FSMContext):
    data = await state.get_data()
    flashcard: Flashcard = data.get("flashcard")
    user: User = data.get("user")
    if not data.get("shared", False):
        try:
            delete(flashcard)
            await query.answer("Карта успешно удалена")
            await query.message.edit_text("Карта успешно удалена.")
        except Exception as e:
            await query.answer("Что-то пошло не так")
            await query.message.edit_text("Что-то пошло не так")
            logging.error(e)
    else:
        try:
            shared_card = get_connection(user.id, flashcard.id)
            delete(shared_card)
            await query.answer("Карта успешно удалена")
            await query.message.edit_text("Карта успешно удалена.")
        except Exception as e:
            await query.answer("Что-то пошло не так")
            await query.message.edit_text("Что-то пошло не так")
            logging.error(e)

    from handle_functions.manage_flashcards import ManageState, reset_menu
    await state.set_state(ManageState.general)
    await reset_menu(query.message, state, True)

@dp.callback_query(DeleteCardCallback.filter(F.delete == False))
async def delete_flashcard(query: CallbackQuery, callback_data: DeleteCardCallback, state: FSMContext):
    await query.answer("Отмена удаления флеш-карты")
    await query.message.edit_text("Карта не была удалена")
    data = await state.get_data()
    if data.get("from_menu", False):
        from handle_functions.manage_flashcards import ManageState, reset_menu
        await state.set_state(ManageState.general)
        await reset_menu(query.message, state, True)
    else:
        await state.clear()
