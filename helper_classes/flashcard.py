class Flashcard:
    def __init__(self, user_id: int | None = None, title: str | None = None, category: str | None = None,
                 question: str | None = None, answer: str | None = None) -> None:
        """
        :param user_id: Идентификатор пользователя
        :param title: Заголовок карты
        :param category: Категория карты
        :param question: Вопрос на карте
        :param answer: Ответ на карте
        """
        self.title = title
        """The title of the card"""
        self.category = category
        """The name of the category of the card"""
        self.question = question
        self.answer = answer
        self.user_id = user_id
        """The telegram user id to which the card belongs"""
        self.allowed_users: set[int] = set()
        """A set of users which can access the card (all but the owner - read only)"""
        self.card_id: int = -1
        """The id of the card in the database"""
        self.local_id: int = -1

    def allow_user(self, user_id: int):
        self.allowed_users.add(user_id)

    def __str__(self) -> str:
        return f"""Flashcard data:
    User id: {self.user_id},
    Title: {self.title},
    Category: {self.category},
    Question: {self.question},
    Answer: {self.answer}"""

    def format(self) -> str:
        assembled = "Флеш-карта:"
        if self.title is not None:
            assembled += f"\n - Заголовок: {self.title}"
        if self.category is not None:
            assembled += f"\n - Категория: {self.category}"
        if self.question is not None:
            assembled += f"\n - Вопрос: {self.question}"
        if self.answer is not None:
            assembled += f"\n - Ответ: {self.answer}"
        return assembled
