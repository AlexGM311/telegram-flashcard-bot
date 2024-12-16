class Flashcard:
    def __init__(self, user_id: int, title: str, category: str, question: str, answer: str) -> None:
        """
        :param user_id: Идентификатор пользователя
        :param title: Заголовок карты
        :param category: Категория карты
        :param question: Вопрос на карте
        :param answer: Ответ на карте
        """
        self.title = title
        self.category = category
        self.question = question
        self.answer = answer
        self.user_id = user_id
        self.allowed_users: set[int] = set()

    def allow_user(self, user_id: int):
        self.allowed_users.add(user_id)

    def __str__(self) -> str:
        return f"""Flashcard data:
    User id: {self.user_id},
    Title: {self.title},
    Category: {self.category},
    Question: {self.question},
    Answer: {self.answer}"""
