from __future__ import annotations

from sqlalchemy import ForeignKey, String, BigInteger, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'Users'

    id: Mapped[BigInteger] = mapped_column(primary_key=True)
    chat_id: Mapped[BigInteger] = mapped_column()
    flashcard_count: Mapped[int] = mapped_column()

    categories: Mapped[list[Category]] = relationship("Category", back_populates="user")

    def __repr__(self):
        return f"User(id={self.id!r}, chat_id={self.chat_id!r}, flashcard_count={self.flashcard_count!r})"


class Category(Base):
    __tablename__ = 'Categories'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[BigInteger] = mapped_column(ForeignKey("Users.id", ondelete="CASCADE"))

    user: Mapped[User] = relationship("User", back_populates="categories")

    def __repr__(self):
        return f"Category(id={self.id!r}, name={self.name!r}, user_id={self.user_id!r})"


class Flashcard(Base):
    __tablename__ = 'Flashcards'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    question: Mapped[str] = mapped_column(String(255))
    answer: Mapped[str] = mapped_column(String(255))
    local_id: Mapped[int] = mapped_column()
    category_id: Mapped[int] = mapped_column(ForeignKey("Categories.id", ondelete="CASCADE"))
    user_id: Mapped[BigInteger] = mapped_column(ForeignKey("Users.id", ondelete="CASCADE"))

    def __repr__(self):
        return f"Flashcard(id={self.id!r}, title={self.title!r}, question={self.question!r}, answer={self.answer!r}, local_id={self.local_id!r}, category_id={self.category_id!r})"


class Statistics(Base):
    __tablename__ = 'Statistics'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    flashcard_id: Mapped[int] = mapped_column(ForeignKey("Flashcards.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id", ondelete="CASCADE"))
    is_correct: Mapped[bool] = mapped_column()
    created_at: Mapped[TIMESTAMP] = mapped_column(default=func.now())

    def __repr__(self):
        return f"Statistics(id={self.id!r}, flashcard_id={self.flashcard_id!r}, is_correct={self.is_correct!r}, created_at={self.created_at!r})"
