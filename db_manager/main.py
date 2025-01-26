from typing import Type
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from db_manager.models import *

session: Session | None = None

def init():
    import os
    from dotenv import load_dotenv
    load_dotenv()

    global session
    # Создать подключение к PostgreSQL
    # noinspection PyPep8Naming
    DATABASE_URL = f'postgresql://{os.getenv("POSTGRE_LOGIN")}:{os.getenv("POSTGRE_PASSWORD")}@{os.getenv("SERVER_ADRESS")}:{os.getenv("SERVER_PORT")}/{os.getenv("DB_NAME")}'
    engine = create_engine(DATABASE_URL)

    # Создать таблицы в базе данных
    BaseTable.metadata.create_all(engine)

    # Добавить столбец notify в БД
    with engine.connect() as connection:
        got = set()
        for row in connection.execute(text(f"SELECT column_name FROM information_schema.columns where table_name='Users'")):
            got.add(row[0])
        if 'notify' not in got:
            connection.execute(text('ALTER TABLE public."Users" ADD COLUMN "notify" BOOLEAN DEFAULT TRUE;'))
        connection.commit()

    # Создание сессии
    s = sessionmaker(engine)
    session = s()


def get_user(telegram_id: int) -> User | None:
    """
    Возвращает пользователя по идентификатору Telegram.

    :param telegram_id: Идентифигатор пользователя в Telegram.
    :return: Словарь {"id": int, "telegram_id": int, "chat_id": int}
    :raises RuntimeError: Если ошибка операции БД.
    """
    # noinspection PyTypeChecker
    return session.get_one(User, telegram_id)

def get_flashcard(card_id: int) -> Flashcard:
    """
    Возвращает флэшкарту по её ID.

    :param card_id: ID получаемой карты в БД.
    :returns: Флеш-карта
    :raises MissingEntryError: Если нет какого-то из параметров карты в БД.
    """
    # noinspection PyTypeChecker
    return session.get_one(Flashcard, card_id)

def get_flashcard_local_user(local_id: int, user: User, force_all_values: bool = True) -> Flashcard | None:
    """
    Возвращает карту по её номеру среди карт пользователя

    :param local_id: Номер карты среди всех карт пользователя
    :param user: Пользователь
    :param force_all_values: Заполнять ли все значения
    :return: Флеш-карта
    """
    return session.query(Flashcard).filter_by(user_id=user.id, local_id=local_id).first()

def update():
    """
    Сохраняет данные в изменённых объектах
    """
    session.commit()

def delete(item) -> None:
    """
    Удаляет флэшкарту.
    :param item: Предмет для удаления.
    :raises RuntimeError: Если ошибка операции БД.
    """
    flag = False
    user: User | None = None
    if isinstance(item, Flashcard):
        flag = True
        user = item.user
    session.delete(item)
    if flag:
        session.commit()
        count = 1
        for flashcard in user.flashcards:
            flashcard.local_id = count
            count += 1

    session.commit()

def get_categories(**kwargs) -> list[Type[Category]]:
    """
    Возвращает список категорий пользователя.

    :param kwargs: По каким параметрам сортировать категории.
    :returns: Список словарей с категориями в формате id: "Название"
    :raises RuntimeError: Если ошибка операции БД.
    """
    return session.query(Category).filter_by(**kwargs).all()


def add(item):
    session.add(item)
    session.commit()

def get_connection(user_id: int, flashcard_id: int) -> FlashcardUser | None:
    """Gets a shared flashcard-user connection."""
    return session.query(FlashcardUser).filter_by(user_id=user_id, flashcard_id=flashcard_id).first()

def get_flashcard_by_uuid(uuid: str) -> Flashcard | None:
    return session.query(Flashcard).filter_by(uuid=uuid).first()

def get_flashcard_user_review(user: User, flashcard: Flashcard) -> CardReview | None:
    return session.query(CardReview).filter_by(user_id=user.id, flashcard_id=flashcard.id).first()

def get_user_due_reviews(user: User) -> list[CardReview]:
    # noinspection PyTypeChecker
    return session.query(CardReview).filter_by(user_id=user.id).filter(CardReview.next_review < datetime.now()).all()

def get_all_due() -> list[CardReview]:
    # noinspection PyTypeChecker
    return session.query(CardReview).filter(CardReview.next_review < datetime.now()).all()


def get_user_card_review(user: User, flashcard: Flashcard) -> CardReview | None:
    return session.query(CardReview).filter_by(user_id=user.id, flashcard_id=flashcard.id).first()

def rollback() -> None:
    session.rollback()
