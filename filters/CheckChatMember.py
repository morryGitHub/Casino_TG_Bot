import asyncio

from aiogram import Bot
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject


class IsBotAdminFilter(BaseFilter):

    async def __call__(self, event: TelegramObject, bot: Bot, chat_id) -> bool:
        chat = await bot.get_chat(chat_id)
        if chat.type == ChatType.PRIVATE:
            # В ЛС админства нет, считаем, что бот "админ"
            return True

        bot_id = (await bot.get_me()).id
        member = await bot.get_chat_member(chat_id, bot_id)

        admin_statuses = [
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        ]
        if member.status not in admin_statuses:
            warn = await event.bot.send_message(
                chat_id=chat_id,
                text="Бот должен быть админом"
            )
            await asyncio.sleep(15)
            await event.bot.delete_message(
                chat_id=chat_id,
                message_id=warn.message_id
            )
            return False
        return True
