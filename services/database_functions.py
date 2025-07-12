import asyncio
import logging
from datetime import datetime, timedelta

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject
from aiomysql import Pool
from aiomysql import Error as AiomysqlError

from db.database import total_bet, users_bet
from db.queries import SELECT_BALANCE, UPDATE_BALANCE_BEFORE_SPIN, SELECT_USER_LANG, UPDATE_BALANCE_AFTER_SPIN, \
    UPDATE_WIN_RESULTS, UPDATE_LOST_RESULTS, SELECT_MAXWIN_RESULTS, SELECT_MAXBET_RESULTS, UPDATE_MAXWIN_RESULTS, \
    UPDATE_MAXBET_RESULTS, UPDATE_USER_ACTIVE, SELECT_DATA_FROM_RESULTS, SELECT_USER_LASTBONUS, UPDATE_USER_LASTBONUS, \
    UPDATE_BALANCE, UPDATE_USER_LANG

BONUS_COOLDOWN = timedelta(hours=24)
BONUS_AMOUNT = 2500


async def get_user_lang(state: FSMContext, user_id: int, dp_pool) -> str:
    data = await state.get_data()
    if 'language' in data:
        return data['language']  # возвращаем из кеша FSM

    # Если нет в FSM — читаем из базы
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(SELECT_USER_LANG, (user_id,))
            row = await cursor.fetchone()
            lang = row[0] if row else 'ru'

    # Сохраняем язык в FSMContext, чтобы в следующий раз не читать из базы
    await state.update_data(language=lang)
    return lang


async def handle_double_bet(callback: CallbackQuery, dp_pool: Pool, user_id: int, double_sum: int) -> None:
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await conn.begin()
                await cursor.execute(SELECT_BALANCE, (user_id,))
                row = await cursor.fetchone()
                if row is None:
                    await callback.message.answer("Ошибка: пользователь не найден в БД.")
                    await conn.rollback()
                    return

                balance = row[0]
                if double_sum > balance:
                    await callback.answer("Недостаточно денег на балансе", show_alert=True)
                    logging.debug(f"Попытка удвоения на {double_sum}, но баланс: {balance}")
                    await conn.rollback()
                    return

                # Списываем средства
                await cursor.execute(UPDATE_BALANCE_BEFORE_SPIN, (double_sum, user_id))

                #  Удваиваем ставки ТОЛЬКО теперь
                for bet in users_bet[user_id]:
                    bet[0] *= 2
                total_bet[user_id] += double_sum
                await conn.commit()

            except AiomysqlError as e:
                await conn.rollback()
                logging.error(f"Ошибка базы данных: {e}")
                await callback.answer("Ошибка работы с базой данных.", show_alert=True)
            except Exception as e:
                await conn.rollback()
                logging.error(f"Неожиданная ошибка: {e}")
                await callback.answer("Произошла ошибка.", show_alert=True)


async def check_user_balance(dp_pool: Pool, user_id):
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(SELECT_BALANCE, (user_id,))
            row = await cursor.fetchone()
            if not row:
                return False
            balance = row[0]
            if balance is None:
                return False
            return int(balance) > 2000


async def update_balance_before_spin(dp_pool: Pool, bet_sum: int, user_id: int) -> None:
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(UPDATE_BALANCE_BEFORE_SPIN, (bet_sum, user_id))


async def update_balance_after_spin(dp_pool: Pool, payout: int, user_id: int) -> None:
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(UPDATE_BALANCE_AFTER_SPIN, (payout, user_id))


async def update_statistics(user_id: int, total_bet_sum: int, total_payout_sum: int, dp_pool: Pool):
    """Обновляет статистику игрока по результатам раунда."""
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            if total_payout_sum > total_bet_sum:
                await cursor.execute(UPDATE_WIN_RESULTS, (total_payout_sum, user_id))
            else:
                await cursor.execute(UPDATE_LOST_RESULTS, (total_bet_sum, user_id))

            await cursor.execute(SELECT_MAXWIN_RESULTS, user_id)
            (maxWin,) = await cursor.fetchone()

            await cursor.execute(SELECT_MAXBET_RESULTS, user_id)
            (maxBet,) = await cursor.fetchone()

            if total_payout_sum > maxWin:
                await cursor.execute(UPDATE_MAXWIN_RESULTS, (total_payout_sum, user_id))

            if total_bet_sum > maxBet:
                await cursor.execute(UPDATE_MAXBET_RESULTS, (total_bet_sum, user_id))


async def check_and_get_valid_bet(
        message: Message,
        dp_pool: Pool,
        user_id: int,
        min_balance: int = 50,
        bet_sum: int | None = None,
) -> int | None:
    """
    Проверяет, есть ли у пользователя нужный баланс.
    Если bet_sum не задана, возвращает max допустимую ставку (balance).
    Возвращает None, если баланса нет.
    """
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(SELECT_BALANCE, (user_id,))
            row = await cursor.fetchone()

            if row is None:
                logging.warning(f"Пользователь {user_id} не найден в БД.")
                return None

            balance = row[0]

            if balance < min_balance:
                warn = await message.answer("Недостаточно денег на балансе.")
                await asyncio.sleep(5)
                await message.delete()
                await warn.delete()
                return None

            if bet_sum is not None and bet_sum > balance:
                warn = await message.answer("Ставка превышает баланс.")
                await asyncio.sleep(5)
                await message.delete()
                await warn.delete()
                return None

            # Если ставка не задана — возвращаем максимально допустимую
            return bet_sum if bet_sum is not None else int(balance)


async def update_user_active(dp_pool: Pool, event: TelegramObject):
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(UPDATE_USER_ACTIVE, (0, event.from_user.id))
            logging.info(f'Пользователь {event.from_user.id} заблокировал бота')


async def get_balance_data(dp_pool: Pool, username: str, user_id: int):
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(SELECT_BALANCE, user_id)
            (balance,) = await cursor.fetchone()
            if not balance:
                balance = 0
                logging.error(f"Cannot get {username} {user_id} = BALANCE")
            await cursor.execute(SELECT_DATA_FROM_RESULTS, (user_id,))
            row = await cursor.fetchone()
            if row:
                winCoin, loseCoin, maxWin, maxBet = row
            return balance, winCoin, loseCoin, maxWin, maxBet


async def get_balance(dp_pool: Pool, user_id):
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(SELECT_BALANCE, user_id)
            (balance,) = await cursor.fetchone()
            return balance


async def update_balance_after_bonus(callback: CallbackQuery, dp_pool: Pool, user_id: int):
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Проверяем дату последнего бонуса
            await cursor.execute(SELECT_USER_LASTBONUS, (user_id,))
            result = await cursor.fetchone()

            now = datetime.now()
            if result and result[0]:
                last_bonus_time = result[0]
                if now - last_bonus_time < BONUS_COOLDOWN:
                    # Ещё рано
                    next_time = last_bonus_time + BONUS_COOLDOWN
                    remaining = next_time - now
                    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                    minutes = remainder // 60
                    await callback.answer(f"Бонус уже получен! Повторно можно через {hours}ч {minutes}м.")
                    return

            if await check_user_balance(dp_pool, user_id):
                await callback.answer("Для бонуса баланс должен быть ниже 2000 монеток.")
                return

            await callback.answer()
            # Выдаём бонус
            await cursor.execute(UPDATE_USER_LASTBONUS, (now, user_id))

            await cursor.execute(UPDATE_BALANCE, (BONUS_AMOUNT, user_id))
            await conn.commit()

            await callback.message.answer(f"🎁 Ты получил бонус +{BONUS_AMOUNT} монет!")


async def update_user_lang(dp_pool: Pool, lang_code: str, user_id: int):
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(UPDATE_USER_LANG, (lang_code, user_id))
