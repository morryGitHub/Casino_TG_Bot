from aiogram.types import TelegramObject, CallbackQuery
from aiomysql import Pool
from db.queries import SELECT_BALANCE
from aiogram.filters import BaseFilter


class CheckBalance(BaseFilter):
    async def __call__(self, event: TelegramObject, dp_pool: Pool, user_id: int) -> bool:

        if dp_pool is None or user_id is None:
            return False

        min_bet = 50
        async with dp_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(SELECT_BALANCE, (user_id,))
                result = await cursor.fetchone()
                if result is None:
                    return False
                balance = result[0]
                if balance < min_bet:
                    if isinstance(event, CallbackQuery):
                        await event.answer("Недостаточно монеток на балансе.")
                    return False
                return True
