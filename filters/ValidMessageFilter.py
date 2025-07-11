from aiogram.types import CallbackQuery
from aiogram.filters import BaseFilter


class ValidMessageFilter(BaseFilter):
    def __init__(self, message_dict: dict):
        self.message_dict = message_dict

    async def __call__(self, callback: CallbackQuery) -> bool:
        if callback.data == "bonus":
            return True

        chat_id = callback.message.chat.id
        if self.message_dict.get(chat_id) != callback.message.message_id:
            await callback.answer("Эта кнопка устарела и недействительна.", show_alert=True)
            return False
        return True
