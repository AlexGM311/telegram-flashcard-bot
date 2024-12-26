import logging
from datetime import datetime
from typing import Any, Optional

import psycopg

from helper_classes import Flashcard, User
from helper_classes.error_types import *
import psycopg as pg

connector: pg.connection.Connection | None = None
cursor: pg.cursor.Cursor | None = None


def initialize_db() -> None:
    global connector, cursor
    connector = pg.connect(password="password", host="localhost", port="5432", dbname="postgres",
                           user="postgres", sslmode="prefer", connect_timeout="10")
    cursor = connector.cursor()
    connector.set_autocommit(True)
    db_name = "testdb"

    try:
        cursor.execute("create database testdb;")
    except pg.errors.DuplicateDatabase:
        logging.error("Database already exists.")
    connector.close()
    cursor.close()
    connector = pg.connect(dbname=db_name, password="password", host="localhost", port="5432",
                           user="postgres", sslmode="prefer", connect_timeout="10")
    cursor = connector.cursor()

    tables = (
        ("""
create table if not exists users (
    telegram_id bigint primary key,
    chat_id bigint,
    flashcard_count integer
);"""[1:],),
        ("""
create table if not exists categories (
    id serial primary key,
    name text,
    user_id integer references users(id) on delete cascade
);"""[1:],),
        ("""
create table if not exists flashcards (
    id serial primary key,
    title text,
    question text,
    answer text,
    local_id integer,
    category_id integer references categories(id) on delete cascade
);"""[1:],),
        ("""
create table if not exists reviews (
    id serial primary key,
    flashcard_id integer references flashcards(id) on delete cascade,
    user_id integer references users(id) on delete cascade,
    next_review timestamp
);"""[1:],),
        ("""
create table if not exists statistics (
    id serial primary key,
    flashcard_id integer references flashcards(id) on delete cascade,
    user_id integer references users(id) on delete cascade,
    is_correct boolean,
    created_at timestamp
);"""[1:],),
        ("""
create table if not exists achievements (
    id serial primary key,
    user_id integer references users(id) on delete cascade,
    achievement text,
    created_at timestamp
);"""[1:],)
    )

    for table in tables:
        cursor.execute(table[0])
    connector.commit()


if __name__ == "__main__":
    initialize_db()

def add_flashcard(flashcard: Flashcard) -> int:
    global cursor
    user = get_user(flashcard.user_id)
    categories = get_categories(user.telegram_id)
    category_id: int = -1
    for category in categories:
        if category['name'] == flashcard.category:
            category_id = category['id']
    if category_id == -1:
        category_id = add_category(flashcard.category, user.telegram_id)
    flashcard.local_id = user.flashcard_count + 1

    cursor.execute("update users set flashcard_count=%s where id=%s",
                   [user.flashcard_count + 1, user.telegram_id])

    cursor.execute("insert into flashcards values (default, %s, %s, %s, %s, %s) returning local_id",
                   [flashcard.title, flashcard.question, flashcard.answer, flashcard.local_id, category_id])

    connector.commit()
    card_id = cursor.fetchall()
    return int(card_id[0][0])

def get_user(telegram_id: int) -> User:
    global cursor
    cursor.execute("select * from users where telegram_id = %s", [telegram_id])
    user = cursor.fetchall()
    if len(user) == 0:
        raise MissingEntryError(f"User {telegram_id} does not exist.")
    user = list(map(int, user[0]))
    return User(user[0], user[1], user[2])

def get_flashcard_user_local(local_id: int, user_id: int, force_all_values: bool = True) -> Flashcard:
    global cursor
    cursor.execute("select * from flashcards join categories on flashcards.category_id=categories.id where categories.user_id=%s and flashcards.local_id=%s", [user_id, local_id])
    fdata = cursor.fetchall()
    if len(fdata) == 0:
        raise MissingEntryError("No flashcard with provided ID and User!")
    fdata = fdata[0]
    card = Flashcard(title=fdata[1], question=fdata[2], answer=fdata[3])
    card.card_id = int(fdata[0])
    card.local_id = int(fdata[4])

    category_id = int(fdata[5])
    cursor.execute("select * from categories where id=%s", [category_id])
    cdata = cursor.fetchall()
    if len(cdata) == 0:
        if not force_all_values:
            return card
        raise MissingEntryError("No category with provided ID!")
    cdata = cdata[0]
    card.category = cdata[1]
    card.user_id = get_user(cdata[2])

    cursor.execute("select * from users where id=%s", [user_id])
    udata = cursor.fetchall()
    if len(udata) == 0:
        if not force_all_values:
            return card
        raise MissingEntryError("No user with proveded ID!")
    udata = udata[0]

    return card

def get_flashcard_db_id(card_id: int, force_all_values: bool = True) -> Flashcard:
    global cursor
    cursor.execute("select * from flashcards where id = %s", [card_id,])
    fdata = cursor.fetchall()
    if len(fdata) == 0:
        raise MissingEntryError("No flashcard with provided ID!")
    fdata = fdata[0]
    card = Flashcard(title=fdata[1], question=fdata[2], answer=fdata[3])
    card.card_id = int(fdata[0])
    card.local_id = int(fdata[4])

    category_id = int(fdata[5])
    cursor.execute("select * from categories where id=%s", [category_id,])
    cdata = cursor.fetchall()
    if len(cdata) == 0:
        if not force_all_values:
            return card
        raise MissingEntryError("No categpry with provided ID!")
    cdata = cdata[0]
    card.category = cdata[1]
    card.user_id = get_user_db_id(int(cdata[2]))['telegram_id']

    user_id = int(cdata[2])
    cursor.execute("select * from users where id=%s", [user_id,])
    udata = cursor.fetchall()
    if len(udata) == 0:
        if not force_all_values:
            return card
        raise MissingEntryError("No user with proveded ID!")
    udata = udata[0]

    return card

def update_flashcard(flashcard: Flashcard) -> None:
    global cursor
    categories = get_categories(flashcard.user_id)
    category = -1
    logging.info(flashcard.category + str(categories))
    for c in categories:
        if c['name'] == flashcard.category:
            category = c['id']
            break
    if category == -1:
        category = add_category(flashcard.category, get_user_telegram_id(flashcard.user_id)['id'])
    cursor.execute("update flashcards set title=%s, question=%s, answer=%s, category_id=%s, local_id=%s where id = %s;",
                   (flashcard.title, flashcard.question, flashcard.answer, category, flashcard.local_id, flashcard.card_id))
    connector.commit()

def delete_flashcard(card_id: int) -> None:
    global cursor
    cursor.execute("delete from flashcards where id=%s", [card_id])
    connector.commit()

def add_category(category_name: str, user_id: int) -> int:
    global cursor
    cursor.execute("insert into categories values (default, %s, %s) returning id",
                   [category_name, user_id])
    connector.commit()
    return int(cursor.fetchall()[0][0])

def get_categories(user_id: int) -> list[dict[str, Any]]:
    global cursor
    uid = get_user_telegram_id(user_id)["id"]
    cursor.execute("select * from categories where user_id = %s", [uid])
    data = cursor.fetchall()
    if len(data) == 0:
        return []
    return [dict(zip(("id", "name", "user_id"), row)) for row in data]

def get_flashcards_by_category(category: int, category_name: Optional[str] = None) -> list[Flashcard]:
    global cursor
    cursor.execute("select * from flashcards where category_id=%s", [category,])
    flashcard_data = cursor.fetchall()
    flashcards: list[Flashcard] = []
    for row in flashcard_data:
        flashcards.append(Flashcard(int(row[0]), category_name, row[1], row[2]))
    return flashcards

def record_answer(card_id: int, user_id: int, is_correct: bool, timestamp: psycopg.Timestamp) -> None:
    global cursor
    if timestamp is None:
        now = datetime.now()
        timestamp = psycopg.Timestamp(now.year, now.month, now.day, now.hour, now.minute, now.second)
    uid = get_user_telegram_id(user_id)['id']
    cursor.execute("insert into statistics values (default, %s, %s, %s, %s) returning id",
                   (card_id, uid, is_correct, timestamp))
    connector.commit()

def get_user_stats(user_id: int) -> dict[str, Any]:
    raise RuntimeError("Not implemented yet")

def reset_user_stats(user_id: int) -> None:
    raise RuntimeError("Not implemented yet")

def schedule_review(user_id: int, card_id: int, next_review_date: str) -> None:
    raise RuntimeError("Not implemented yet")

def get_scheduled_reviews(user_id: int, date: str) -> list[Flashcard]:
    raise RuntimeError("Not implemented yet")

def get_flashcards_by_user(user_id: int) -> list[Flashcard]:
    raise RuntimeError("Not implemented yet")

def add_user(telegram_id: int, chat_id: int) -> None:
    global cursor
    cursor.execute("insert into users values (%s, %s, 0)",
                   [telegram_id, chat_id])
    connector.commit()
