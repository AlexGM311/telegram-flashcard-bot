import datetime
from typing import Any, Optional

import psycopg

from helper_classes import Flashcard
import db_manager.functions

def initialize_db() -> None:
    """
    Инициализирует базу данных, создавая необходимые таблицы.
    :raises RuntimeError: Если ошибка операции БД.
    """
    return functions.initialize_db()

def add_flashcard(flashcard: Flashcard) -> int:
    """
    Добавляет новую флэшкарту.

    :param flashcard: Флэшкарта со всеми её параметрами.
    :returns: ID добавленной карты в базе данных.
    :raises RuntimeError: Если ошибка операции БД.
    """
    return functions.add_flashcard(flashcard)

def get_user(telegram_id: int) -> dict[str, int]:
    """
    Возвращает пользователя по идентификатору Telegram.

    :param telegram_id: Идентифигатор пользователя в Telegram.
    :return: Словарь {"id": int, "telegram_id": int, "chat_id": int}
    :raises RuntimeError: Если ошибка операции БД.
    """
    return functions.get_user(telegram_id)

def get_flashcard(card_id: int, force_all_values: bool = True) -> Flashcard:
    """
    Возвращает флэшкарту по её ID.

    :param force_all_values: Заполнять ли все параметры карты. Если да, то при отсутсвии какого-то параметра в БД будет ошибка MissingEntryError
    :param card_id: ID получаемой карты в БД.
    :returns: Флеш-карта
    :raises MissingEntryError: Если нет какого-то из параметров карты в БД.
    """
    return functions.get_flashcard_db_id(card_id, force_all_values)

def get_flashcard_local_user(local_id: int, user_id: int, force_all_values: bool = True) -> Flashcard:
    """
    Возвращает карту по её номеру среди карт пользователя

    :param local_id: Номер карты среди всех карт пользователя
    :param user_id: Идентификатор пользователя в БД
    :param force_all_values: Заполнять ли все значения
    :return: Флеш-карта
    """
    return functions.get_flashcard_user_local(local_id, user_id, force_all_values)

def update_flashcard(flashcard: Flashcard) -> None:
    """
    Обновляет данные флэшкарты.

    :param flashcard: Новые данные для флэшкарты.
    :raises RuntimeError: Если ошибка операции БД.
    """
    return functions.update_flashcard(flashcard)

def delete_flashcard(card_id: int) -> None:
    """
    Удаляет флэшкарту.

    :param card_id: ID флэшкарты.
    :returns: True, если удаление успешно, иначе False.
    :raises RuntimeError: Если ошибка операции БД.
    """
    return functions.delete_flashcard(card_id)

def add_category(category_name: str, user_id: int) -> int:
    """
    Добавляет новую категорию.

    :param category_name: Название категории.
    :param user_id: ID пользователя.
    :returns: ID созданной категории.
    :raises RuntimeError: Если ошибка операции БД.
    """
    return functions.add_category(category_name, user_id)

def get_categories(user_id: int) -> list[dict[str, Any]]:
    """
    Возвращает список категорий пользователя.

    :param user_id: ID пользователя.
    :returns: Список словарей с категориями в формате id: "Название"
    :raises RuntimeError: Если ошибка операции БД.
    """
    return functions.get_categories(user_id)

def get_flashcards_by_category(category: int, category_name: Optional[str] = None) -> list[Flashcard]:
    """
    Возвращает флэшкарты из указанной категории.

    :param category_name: Название категории, опционально. Если не предоставлено, подставляет None.
    :param category: ID категории.
    :returns: Список флэшкартами.
    :raises RuntimeError: Если ошибка операции БД.
    """
    return functions.get_flashcards_by_category(category, category_name)

def record_answer(card_id: int, user_id: int, is_correct: bool, next_review: psycopg.Timestamp = None) -> None:
    """
    Сохраняет результат ответа пользователя.

    :param next_review: Когда запланировать следующее повторение карточки.
    :param card_id: ID флэшкарты.
    :param user_id: ID пользователя.
    :param is_correct: Был ли ответ правильным.
    :raises RuntimeError: Если ошибка операции БД.
    """
    return functions.record_answer(card_id, user_id, is_correct, next_review)

def get_user_stats(user_id: int) -> dict[str, Any]:
    """
    Возвращает статистику пользователя.

    :param user_id: ID пользователя.
    :returns: Словарь с данными статистики в формате "Название":метрика (int, float, bool)
    :raises RuntimeError: Если ошибка операции БД.
    """
    return functions.get_user_stats(user_id)

def reset_user_stats(user_id: int) -> None:
    """
    Сбрасывает статистику пользователя.

    :param user_id: ID пользователя.
    :returns: True, если сброс успешен, иначе False.
    :raises RuntimeError: Если ошибка операции БД.
    """
    return functions.reset_user_stats(user_id)

def schedule_review(user_id: int, card_id: int, next_review_date: str) -> None:
    """
    Запланировать повтор флэшкарты.

    :param user_id: ID пользователя.
    :param card_id: ID флэшкарты.
    :param next_review_date: Дата следующего повторения (в формате 'YYYY-MM-DD').
    :raises RuntimeError: Если ошибка операции БД.
    """
    return functions.schedule_review(user_id, card_id, next_review_date)

def get_scheduled_reviews(user_id: int, date: datetime) -> list[Flashcard]:
    """
    Возвращает флэшкарты, запланированные для повторения на указанную дату.

    :param user_id: ID пользователя.
    :param date: Дата, на которую нужны запланированные флеш-карты
    :returns: Список флешкарт.
    :raises RuntimeError: Если ошибка операции БД.
    """
    return functions.get_scheduled_reviews(user_id, date)

def get_flashcards_by_user(user_id: int) -> list[Flashcard]:
    """
    Возвращает флешкарты, созданные или доступные определённому пользователю.

    :param user_id:
    :return: Список флеш-карт типа Flashcard
    :raises RuntimeError: Если ошибка операции БД.
    """
    return functions.get_flashcards_by_user(user_id)

def add_user(telegram_id: int, chat_id: int):
    """
    Добавляет пользователя в БД.

    :param telegram_id: Идентфиикатор пользователя в Telegram.
    :param chat_id: Идентификатор чата с пользователем в Telegram.
    """
    functions.add_user(telegram_id, chat_id)
