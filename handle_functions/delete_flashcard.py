import logging

from aiogram import F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import *
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.methods import edit_message_text

import db_manager
from handle_functions.dp import dp
from helper_classes import Flashcard
from helper_classes.error_types import DatabaseError, MissingEntryError


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

@dp.message(Command("delete_flashcard"))
async def delete_flashcard_handler(message: Message, state: FSMContext):
    await message.answer(
        "Введите идентификатор удаляемой флеш-карты",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(DeleteFlashcard.id)
    await state.update_data(
        bot=message.bot,
        message_id=message.message_id,
        chat_id=message.chat.id,
        message_text="Введите идентификатор удаляемой флеш-карты"
    )

@dp.message(DeleteFlashcard.id)
async def delete_id(message: Message, state: FSMContext):
    data = await state.get_data()

    try:
        card_id = int(message.text)
        user = db_manager.get_user_telegram_id(message.from_user.id)
        flashcard: Flashcard = db_manager.get_flashcard_local_user(card_id, user['id'])
        await message.answer(
            f"Вы уверены, что хотите удалить флеш-карту:\n" + flashcard.format(),
            reply_markup=DeleteFlashcard.markup
        )
        await state.update_data(flashcard=flashcard)
    except ValueError as e:
        if data["message_text"] != f"Не удалось преобразовать {message.text} в число. Попробуйте снова":
            await edit_message_text.EditMessageText(
                text=f"Не удалось преобразовать {message.text} в число. Попробуйте снова"
            )
            await state.update_data(message_text=f"Не удалось преобразовать {message.text} в число. Попробуйте снова")
        await message.delete()
        logging.error(e)

    except MissingEntryError as e:
        await message.answer("Такой карты не существует!")
        await state.clear()

@dp.callback_query(DeleteCardCallback.filter(F.delete == True))
async def delete_flashcard(query: CallbackQuery, callback_data: DeleteCardCallback, state: FSMContext):
    data = await state.get_data()
    flashcard: Flashcard = data["flashcard"]
    try:
        db_manager.delete_flashcard(flashcard.card_id)
        await query.answer("Карта успешно удалена")
        await query.message.edit_text("Карта успешно удалена.")
    except DatabaseError as e:
        await query.answer("Что-то пошло не так")
        await query.message.edit_text("Что-то пошло не так")
        logging.error(e)
    await state.clear()

@dp.callback_query(DeleteCardCallback.filter(F.delete == False))
async def delete_flashcard(query: CallbackQuery, callback_data: DeleteCardCallback, state: FSMContext):
    await query.answer("Отмена удаления флеш-карты")
    await query.message.edit_text("Карта не была удалена")
    await state.clear()
