import logging

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject
from aiomysql import Pool

from db.queries import SELECT_USER_LANG


class LanguageMiddleware(BaseMiddleware):
    def __init__(self, dp_pool: Pool, default_lang='ru'):
        self.dp_pool = dp_pool
        self.default_lang = default_lang
        super().__init__()

    async def __call__(self, handler, event: TelegramObject, data: dict):
        state: FSMContext = data.get('state')
        user = getattr(event, 'from_user', None)

        if user is None or not state:
            return await handler(event, data)

        user_id = user.id
        logging.debug("1")

        # Сначала пробуем достать язык из FSMContext
        fsm_data = await state.get_data()
        lang = fsm_data.get('language')
        logging.debug("2")

        if not lang:
            logging.debug("3")
            # Если нет — грузим из базы
            async with self.dp_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(SELECT_USER_LANG, (user_id,))
                    row = await cursor.fetchone()
                    lang = row[0] if row else self.default_lang

            await state.update_data(language=lang)

        logging.debug(lang)
        logging.debug(data['user_lang'])
        data['user_lang'] = lang
        return await handler(event, data)
