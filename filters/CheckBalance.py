import logging

from aiogram.types import TelegramObject
from aiomysql import Pool
from db.queries import SELECT_BALANCE
from aiogram.filters import BaseFilter


class CheckBalance(BaseFilter):
    async def __call__(self, event: TelegramObject, dp_pool: Pool, user_id: int) -> bool:
        logging.debug(f"CheckBalance filter: dp_pool={dp_pool}, user_id={user_id}")

        if dp_pool is None or user_id is None:
            logging.debug("CheckBalance filter: missing dp_pool or user_id")
            return False

        min_bet = 0
        async with dp_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(SELECT_BALANCE, (user_id,))
                result = await cursor.fetchone()
                logging.debug(f"CheckBalance filter: balance query result={result}")
                if result is None:
                    return False
                balance = result[0]
                logging.debug(f"CheckBalance filter: balance={balance}, min_bet={min_bet}")
                return balance >= min_bet
