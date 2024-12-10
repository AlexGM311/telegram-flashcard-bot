from typing import Any

from obj.flashcard import Flashcard

def initialize_db() -> None:
    """
    Инициализирует базу данных, создавая необходимые таблицы.
    :raises RuntimeError: Если ошибка операции БД.
    """
    pass

def add_flashcard(flashcard: Flashcard) -> int:
    """
    Добавляет новую флэшкарту.

    :param flashcard: Флэшкарта со всеми её параметрами.
    :returns: ID добавленной карты в базе данных.
    :raises RuntimeError: Если ошибка операции БД.
    """
    raise RuntimeError("Not implemented yet")


def get_flashcard(card_id: int) -> dict:
    """
    Возвращает флэшкарту по её ID.

    :param card_id: ID получаемой карты в БД.
    :returns: Словарь с данными флэшкарты.
    :raises RuntimeError: Если ошибка операции БД.
    """
    raise RuntimeError("Not implemented yet")


def update_flashcard(card_id: int, flashcard: Flashcard) -> None:
    """
    Обновляет данные флэшкарты.

    :param card_id: Идентификатор карты в БД.
    :param flashcard: Новые данные для флэшкарты.
    :raises RuntimeError: Если ошибка операции БД.
    """
    raise RuntimeError("Not implemented yet")


def delete_flashcard(card_id: int) -> None:
    """
    Удаляет флэшкарту.

    :param card_id: ID флэшкарты.
    :returns: True, если удаление успешно, иначе False.
    :raises RuntimeError: Если ошибка операции БД.
    """
    raise RuntimeError("Not implemented yet")


def add_category(category_name: str, user_id: int) -> int:
    """
    Добавляет новую категорию.

    :param category_name: Название категории.
    :param user_id: ID пользователя.
    :returns: ID созданной категории.
    :raises RuntimeError: Если ошибка операции БД.
    """
    raise RuntimeError("Not implemented yet")


def get_categories(user_id: int) -> list[dict[int, str]]:
    """
    Возвращает список категорий пользователя.

    :param user_id: ID пользователя.
    :returns: Список словарей с категориями в формате id: "Название"
    :raises RuntimeError: Если ошибка операции БД.
    """
    raise RuntimeError("Not implemented yet")


def get_flashcards_by_category(category: int) -> list[Flashcard]:
    """
    Возвращает флэшкарты из указанной категории.

    :param category: ID категории.
    :returns: Список флэшкартами.
    :raises RuntimeError: Если ошибка операции БД.
    """
    raise RuntimeError("Not implemented yet")


def record_answer(card_id: int, user_id: int, is_correct: bool) -> None:
    """
    Сохраняет результат ответа пользователя.

    :param card_id: ID флэшкарты.
    :param user_id: ID пользователя.
    :param is_correct: Был ли ответ правильным.
    :raises RuntimeError: Если ошибка операции БД.
    """
    raise RuntimeError("Not implemented yet")


def get_user_stats(user_id: int) -> dict[str, Any]:
    """
    Возвращает статистику пользователя.

    :param user_id: ID пользователя.
    :returns: Словарь с данными статистики в формате "Название":метрика (int, float, bool)
    :raises RuntimeError: Если ошибка операции БД.
    """
    raise RuntimeError("Not implemented yet")


def reset_user_stats(user_id: int) -> None:
    """
    Сбрасывает статистику пользователя.

    :param user_id: ID пользователя.
    :returns: True, если сброс успешен, иначе False.
    :raises RuntimeError: Если ошибка операции БД.
    """
    raise RuntimeError("Not implemented yet")


def schedule_review(user_id: int, card_id: int, next_review_date: str) -> None:
    """
    Запланировать повтор флэшкарты.

    :param user_id: ID пользователя.
    :param card_id: ID флэшкарты.
    :param next_review_date: Дата следующего повторения (в формате 'YYYY-MM-DD').
    :raises RuntimeError: Если ошибка операции БД.
    """
    raise RuntimeError("Not implemented yet")


def get_scheduled_reviews(user_id: int, current_date: str) -> list[Flashcard]:
    """
    Возвращает флэшкарты, запланированные для повторения на указанную дату.

    :param user_id: ID пользователя.
    :param current_date: Текущая дата (в формате 'YYYY-MM-DD').
    :returns: Список флешкарт.
    :raises RuntimeError: Если ошибка операции БД.
    """
    raise RuntimeError("Not implemented yet")
