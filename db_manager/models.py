from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import ForeignKey, String, BigInteger, func, UUID, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from math import pi

pi_twentieth = 20/pi

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'Users'

    id = mapped_column(BigInteger, primary_key=True)
    chat_id = mapped_column(BigInteger)

    categories: Mapped[list[Category]] = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    flashcards: Mapped[list[Flashcard]] = relationship("Flashcard", back_populates="user", order_by="Flashcard.local_id", cascade="all, delete-orphan")
    shared_flashcards = relationship("FlashcardUser", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("CardReview", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"User(id={self.id!r}, chat_id={self.chat_id!r})"


class Category(Base):
    __tablename__ = 'Categories'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[BigInteger] = mapped_column(ForeignKey(User.id, ondelete="CASCADE"))

    user: Mapped[User] = relationship("User", back_populates="categories")
    flashcards: Mapped[list[Flashcard]] = relationship("Flashcard", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Category(id={self.id!r}, name={self.name!r}, user_id={self.user_id!r})"

class Flashcard(Base):
    __tablename__ = 'Flashcards'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    question: Mapped[str] = mapped_column(String(255))
    answer: Mapped[str] = mapped_column(String(255))
    local_id: Mapped[int] = mapped_column(default=func.count())
    category_id = mapped_column(ForeignKey(Category.id, ondelete="CASCADE"))
    user_id = mapped_column(ForeignKey(User.id, ondelete="CASCADE"))
    uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), unique=True, server_default=text("uuid_generate_v4()"))

    user: Mapped[User] = relationship("User", back_populates="flashcards")
    category: Mapped[Category] = relationship("Category", back_populates="flashcards")

    shared_users = relationship("FlashcardUser", back_populates="flashcard", cascade="all, delete-orphan")
    reviews = relationship("CardReview", back_populates="flashcard", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Flashcard(id={self.id!r}, title={self.title!r}, question={self.question!r}, answer={self.answer!r}, local_id={self.local_id!r}, category_id={self.category_id!r})"

    def format(self) -> str:
        assembled = "Флеш-карта:"
        if self.title is not None:
            assembled += f"\n - Заголовок: {self.title}"
        if self.category is not None:
            assembled += f"\n - Категория: {self.category.name}"
        if self.question is not None:
            assembled += f"\n - Вопрос: {self.question}"
        if self.answer is not None:
            assembled += f"\n - Ответ: {self.answer}"
        return assembled

    def __str__(self) -> str:
        return f"""Flashcard data:
    ID: {self.id}
    User id: {self.user_id},
    Title: {self.title},
    Category: {self.category.name},
    Question: {self.question},
    Answer: {self.answer}"""

class FlashcardUser(Base):
    __tablename__ = 'FlashcardUser'

    flashcard_id: Mapped[int] = mapped_column(ForeignKey(Flashcard.id, ondelete='CASCADE'), primary_key=True)
    user_id: Mapped[BigInteger] = mapped_column(ForeignKey(User.id, ondelete='CASCADE'), primary_key=True)

    flashcard = relationship("Flashcard", back_populates="shared_users")
    user = relationship("User", back_populates="shared_flashcards")

class CardReview(Base):
    __tablename__ = 'CardReview'

    flashcard_id: Mapped[int] = mapped_column(ForeignKey(Flashcard.id, ondelete='CASCADE'), primary_key=True)
    user_id: Mapped[BigInteger] = mapped_column(ForeignKey(User.id, ondelete='CASCADE'), primary_key=True)

    flashcard = relationship("Flashcard", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

    ease_factor: Mapped[float] = mapped_column()
    interval: Mapped[int] = mapped_column(default=1)
    last_reviewed: Mapped[datetime] = mapped_column(default=datetime.now())
    next_review: Mapped[datetime] = mapped_column(default=datetime.now())
    review_count: Mapped[int] = mapped_column(default=0)

    # noinspection PyTypeChecker
    def update_review(self, quality: int):
        if quality < 3:
            self.interval = 1
            self.review_count = 0
            self.ease_factor = self.ease_factor ** 0.85
        else:
            self.review_count += 1
            if self.review_count == 1:
                self.interval = 1
            elif self.review_count == 2:
                self.interval = 2
            else:
                self.interval = min(int(self.interval * self.ease_factor), 7)  # Up to a week
        if not self.ease_factor:
            self.ease_factor = 1
        else:
            from math import atan, tan, pi
            n = self.ease_factor
            arc = n / pi_twentieth
            angle = tan(arc) * 5
            angle += 1
            n = pi_twentieth * atan(angle / 5)
            self.ease_factor = n

        self.next_review = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.next_review += timedelta(days=self.interval)
