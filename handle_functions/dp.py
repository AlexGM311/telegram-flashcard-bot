from aiogram import Dispatcher
dp: Dispatcher | None = None

def set_dp(dp_new: Dispatcher):
    global dp
    dp = dp_new

def safe_callback_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            import logging
            from db_manager.main import rollback
            logging.error(f"Error occurred in {func.__name__}: {e} Rolled back the DB transaction.", exc_info=True)
            if 'query' in kwargs and isinstance(kwargs['query'], CallbackQuery):
                kwargs['query'].answer("An error occurred. Please try again later.", show_alert=True)
            elif len(args) > 0 and isinstance(args[0], CallbackQuery):
                args[0].answer("An error occurred. Please try again later.", show_alert=True)
            rollback()
    return wrapper
