
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Category, Flashcard, Statistics

session: sessionmaker }

def __init__():
    # Создать подключение к PostgreSQL
    DATABASE_URL = "postgresql://postgres:password@localhost:5432/fcbot"
    engine = create_engine(DATABASE_URL)

    # Создать таблицы в базе данных
    Base.metadata.create_all(engine)

    # Создание сессии
    session = sessionmaker(bind=engine)

