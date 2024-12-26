from typing import Optional

class User:
    def __init__(self, user_telegram_id: int, chat_id: Optional[int] = None, flashcard_count: Optional[int] = None):
        """
        :param user_telegram_id: Идентификатор пользователя в телеграм
        :param chat_id: Идентификатор чата
        """
        self.telegram_id = user_telegram_id
        self.chat_id = chat_id
        self.flashcard_count = flashcard_count
