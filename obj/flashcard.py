class Flashcard:
    def __init__(self, title: str, category: str, question: str, answer: str):
        """
        :param title: Заголовок карты
        :param category: Категория карты
        :param question: Вопрос на карте
        :param answer: Ответ на карте
        """
        self.title = title
        self.category = category
        self.question = question
        self.answer = answer
