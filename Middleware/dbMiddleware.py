import logging

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Any
from aiomysql import Pool, Cursor
from db.queries import CHECK_USER_EXISTS, INSERT_USER_INTO_USERS, INSERT_USER_INTO_BALANCES, UPDATE_USER_ACTIVE, \
    SELECT_USER_ACTIVITY, INSERT_USER_INTO_RESULTS


class DbMiddleware(BaseMiddleware):
    def __init__(self, pool):
        self.pool = pool

    async def __call__(self, handler: Callable[[TelegramObject, dict], Any], event: TelegramObject, data: dict):
        data["dp_pool"] = self.pool
        return await handler(event, data)


class CheckUserMiddleware(BaseMiddleware):
    def __init__(self, pool):
        self.pool: Pool = pool

    async def __call__(self, handler: Callable[[TelegramObject, dict], Any], event: TelegramObject, data: dict):
        # Попытка получить пользователя из event
        user = None
        chat = None

        if hasattr(event, "from_user") and event.from_user:
            user = event.from_user
            chat = event.chat
        elif hasattr(event, "message") and event.message and event.message.from_user:
            user = event.message.from_user
            chat = event.message.chat
        elif hasattr(event, "callback_query") and event.callback_query and event.callback_query.from_user:
            user = event.callback_query.from_user
            chat = event.callback_query.message.chat

        if user is None:
            # Просто пропускаем или логируем
            logging.warning("Нет from_user в событии, пропускаем middleware")
            return await handler(event, data)

        username = user.username or "Unknown"
        user_id = user.id
        chat_id = chat.id
        data["user_id"] = user_id
        data["username"] = username
        data["chat_id"] = chat_id

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                cursor: Cursor
                await cursor.execute(CHECK_USER_EXISTS, user_id)
                (exist,) = await cursor.fetchone()

                if not exist:
                    await cursor.execute(INSERT_USER_INTO_USERS, (user_id, chat_id, username, 1))
                    await cursor.execute(INSERT_USER_INTO_BALANCES, (user_id, 2000))
                    await cursor.execute(INSERT_USER_INTO_RESULTS, (user_id, 0, 0, 0, 0))

                    logging.debug(f'INSERT_USER_INTO_USERS => {user_id, username}')
                    logging.debug(f'INSERT_USER_INTO_BALANCES => {user_id}')
                    logging.debug(f'INSERT_USER_INTO_RESULTS => {user_id}')
                    message = event.message or event.callback_query.message
                    # await language_handle(message)
                await cursor.execute(SELECT_USER_ACTIVITY, user_id)
                (active,) = await cursor.fetchone()
                if active == 0:
                    await cursor.execute(UPDATE_USER_ACTIVE, (1, user_id))

        return await handler(event, data)
