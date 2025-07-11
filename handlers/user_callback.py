import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiomysql import Pool, Cursor

from filters.CheckBalance import CheckBalance
from filters.ValidMessageFilter import ValidMessageFilter
from lexicon.colors import COLOR_EMOJIS
from aiomysql import Error as AiomysqlError

from FSM.FSM import GameStates
from db.database import user_messages, bet_messages, roulette_messages, users_bet, total_bet, double_messages
from db.queries import SELECT_BALANCE, UPDATE_BALANCE_BEFORE_SPIN, UPDATE_BALANCE_AFTER_SPIN, UPDATE_USER_LANG, \
    UPDATE_WIN_RESULTS, UPDATE_LOST_RESULTS, SELECT_USER_LASTBONUS, UPDATE_USER_LASTBONUS, UPDATE_BALANCE
from services.roulette_logic import spin_roulette, calculate_win_and_payout
from services.updates import clear_dicts, end_roulette, delete_user_messages, delete_double_messages, delete_bet_mes

BONUS_COOLDOWN = timedelta(hours=24)
BONUS_AMOUNT = 2500

user_callback = Router()


@user_callback.callback_query(ValidMessageFilter(roulette_messages), (F.data.startswith("bet_")), CheckBalance())
async def bet_handler(callback: CallbackQuery, state: FSMContext, username, dp_pool: Pool, user_id):
    await callback.answer()
    bet_data = callback.data.split("_")
    bet_sum = int(bet_data[1])  # 500, преобразуем в int
    bet_range_or_color = bet_data[2]  # например, "1-18"

    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            cursor: Cursor
            await cursor.execute(SELECT_BALANCE, user_id)
            row = await cursor.fetchone()
            if row is None:
                logging.warning("Недостаточно денег на балансе ")
                return
            balance = row[0]
            if not (bet_sum <= balance):
                await callback.answer("Недостаточно денег на балансе", show_alert=True)
                logging.debug("Недостаточно денег на балансе")
                return

    bet_color = None
    if bet_range_or_color in ['red', 'green', 'black']:
        bet_color = COLOR_EMOJIS[bet_range_or_color]

    # Если пользователь уже ставил, добавляем новую ставку в список
    if user_id in users_bet:
        logging.debug(users_bet[user_id])

        # Проверяем, есть ли уже ставка на этот bet_range_or_color
        for bet in users_bet[user_id]:
            if bet[1] == bet_range_or_color:
                bet[0] += bet_sum  # Увеличиваем сумму
                action = "увеличена"
                total_bet[user_id] += bet_sum

                break
        else:
            # Если такой ставки не было, добавляем новую
            users_bet[user_id].append([bet_sum, bet_range_or_color, username])
            action = "принята"
            total_bet[user_id] += bet_sum
    else:
        # Если это первая ставка пользователя
        users_bet[user_id] = [[bet_sum, bet_range_or_color, username]]
        action = "принята"
        total_bet[user_id] = bet_sum
        await state.set_state(GameStates.waiting_for_bet)

    # Отправляем сообщение
    bet_message = await callback.message.answer(
        text=f"""Ставка {action}: <a href="tg://user?id={user_id}">{username}</a> {bet_sum} монет на {bet_color or bet_range_or_color}""",
        parse_mode="HTML"
    )

    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(UPDATE_BALANCE_BEFORE_SPIN, (bet_sum, user_id))
            logging.debug('Your bet is successful')

    if user_id not in bet_messages:
        bet_messages[user_id] = []

    bet_messages[user_id].append({
        "chat_id": bet_message.chat.id,
        "message_id": bet_message.message_id
    })


@user_callback.callback_query(ValidMessageFilter(roulette_messages), (F.data == 'spin'), GameStates.waiting_for_bet)
async def spin_handler(callback: CallbackQuery, bot: Bot, state: FSMContext, dp_pool: Pool, username, user_id, chat_id):
    number, color = spin_roulette()

    await state.update_data(bet_result=(number, color))
    await callback.message.delete()

    bet_results = []
    total_bet_sum = 0
    total_payout_sum = 0

    for uid, bets in users_bet.items():
        for bet in bets:
            amount, target, username = bet
            total_bet_sum += amount
            is_win, payout = calculate_win_and_payout(number, color, target, amount)

            if is_win:
                total_payout_sum += payout
                bet_results.append(
                    f"💲 <a href='tg://user?id={uid}'>{username}</a> выиграл {payout} на {COLOR_EMOJIS.get(target, target)}")

                async with dp_pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute(UPDATE_BALANCE_AFTER_SPIN, (payout, user_id))

            bet_results.append(f"🐾 {username} {amount} на {COLOR_EMOJIS.get(target, target)}")

    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            if total_payout_sum > total_bet_sum:
                await cursor.execute(UPDATE_WIN_RESULTS, (total_payout_sum - total_bet_sum, user_id))
            else:
                await cursor.execute(UPDATE_LOST_RESULTS, (total_bet_sum - total_payout_sum, user_id))

    await delete_bet_mes(bot)
    clear_dicts()
    await state.clear()

    mes_spin = await callback.message.answer(
        f'<a href="tg://user?id={user_id}">{username}</a> крутит...(3 сек)',
        parse_mode="HTML"
    )

    bot_message = await bot.send_animation(
        chat_id=chat_id,
        animation='CgACAgQAAxkBAAIBTWhhY9tM5QKXejsi-QvzHNXRXgLMAALVAgACuiENU9OiouXPz52yNgQ'
    )

    # Сохраняем ID сообщений
    user_messages[user_id] = {
        "chat_id": chat_id,
        "user_msg": mes_spin.message_id,
        "bot_msg": bot_message.message_id,
    }

    await asyncio.sleep(3)

    await delete_user_messages(bot)
    logging.debug('try delete_double_messages()')
    await delete_double_messages(bot)

    sorted_lines = sorted(bet_results, key=lambda s: s.split()[0])  # Сортируем список строк
    text_sorted = "\n".join(sorted_lines)

    await callback.message.answer(
        text=f"🎯 Выпал номер: {number} {COLOR_EMOJIS[color]}\n"
             f"{text_sorted}",
        parse_mode="HTML"
    )
    await end_roulette(chat_id=chat_id)
    clear_dicts()


@user_callback.callback_query(ValidMessageFilter(roulette_messages), F.data == 'spin')
async def spin_wrong_state(callback: CallbackQuery):
    await callback.answer("Сначала сделайте ставку!")


@user_callback.callback_query(ValidMessageFilter(roulette_messages), F.data == 'double')
async def double_bet(callback: CallbackQuery, bot: Bot, dp_pool: Pool, user_id, username):
    if user_id not in users_bet or not users_bet[user_id]:
        await callback.answer("Сначала сделайте ставку")
        return
    logging.debug(users_bet)

    bets_text = f"{username} удвоил все свои ставки:\n"
    # 1. Считаем сумму удвоения, НЕ модифицируя ставки
    new_total = sum(bet[0] for bet in users_bet[user_id])  # сумма текущих ставок
    double_sum = new_total  # столько нужно списать с баланса

    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await conn.begin()
                # 2. Проверка баланса
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

                # 3. Списываем средства
                await cursor.execute(UPDATE_BALANCE_BEFORE_SPIN, (double_sum, user_id))

                # 4. Удваиваем ставки ТОЛЬКО теперь
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

    # Формируем красивый ответ
    bets_text += "\n".join(
        [f"💰 {b[0]} на {COLOR_EMOJIS.get(b[1], b[1])}" for b in users_bet[user_id]]
    )

    if user_id in double_messages:
        try:
            await bot.edit_message_text(
                text=f"{bets_text}\nОбщая ставка: {total_bet[user_id]}",
                chat_id=double_messages[user_id]["chat_id"],
                message_id=double_messages[user_id]["message_id"]
            )
        except TelegramBadRequest as e:
            logging.warning(f"Не удалось изменить сообщение: {e}")
    else:
        double_message = await callback.message.answer(f"{bets_text}\nОбщая ставка: {total_bet[user_id]}")

        double_messages[user_id] = {
            "chat_id": double_message.chat.id,
            "message_id": double_message.message_id
        }


@user_callback.callback_query(ValidMessageFilter(roulette_messages), F.data == 'cancel')
async def spin_wrong_state(callback: CallbackQuery, bot: Bot, state: FSMContext, username, user_id, dp_pool: Pool):
    if user_id not in users_bet or not users_bet[user_id]:
        await callback.answer("Сначала сделайте ставку")
        return

    await delete_bet_mes(bot)
    await delete_double_messages(bot)
    await state.clear()

    total = total_bet[user_id]
    await callback.answer(f"{username} ваши ставки были отменены")

    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(UPDATE_BALANCE_AFTER_SPIN, (total, user_id))

    clear_dicts()


@user_callback.callback_query(F.data == "bonus")
async def process_bonus(callback: CallbackQuery, dp_pool: Pool, user_id):
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

            await callback.answer()
            # Выдаём бонус
            await cursor.execute(UPDATE_USER_LASTBONUS, (now, user_id))

            await cursor.execute(UPDATE_BALANCE, (BONUS_AMOUNT, user_id))
            await conn.commit()

            await callback.message.answer(f"🎁 Ты получил бонус +{BONUS_AMOUNT} монет!")


@user_callback.callback_query(F.data.startswith("lang_"))
async def process_language_choice(callback: CallbackQuery, state: FSMContext, dp_pool: Pool, user_id):
    lang_code = callback.data.split('_')[1]

    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(UPDATE_USER_LANG, (lang_code, user_id))

    await state.update_data(language=lang_code)

    await callback.answer(f"Язык установлен: {lang_code.upper()}")
    await callback.message.answer(f"Выбран язык: {lang_code.upper()}")
    await callback.message.delete()
