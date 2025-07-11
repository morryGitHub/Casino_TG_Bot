import asyncio
import logging

from aiogram import Bot, Router, F
from aiogram.filters import CommandStart, Command, or_f, ChatMemberUpdatedFilter, KICKED
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ChatMemberUpdated
from aiomysql import Pool, Cursor

from FSM.FSM import GameStates
from db.database import user_messages, roulette_messages, bet_messages, users_bet, roulette_states, total_bet
from db.queries import SELECT_BALANCE, UPDATE_BALANCE_BEFORE_SPIN, UPDATE_BALANCE_AFTER_SPIN, UPDATE_USER_ACTIVE, \
    SELECT_DATA_FROM_RESULTS, UPDATE_WIN_RESULTS, UPDATE_LOST_RESULTS, SELECT_MAXWIN_RESULTS, SELECT_MAXBET_RESULTS, \
    UPDATE_MAXWIN_RESULTS, UPDATE_MAXBET_RESULTS
from filters.CheckChatMember import IsBotAdminFilter
from keyboards.user_kb import start_buttons, bets_keyboards, bonus_button
from lexicon.Lexicon import lexicon
from services.roulette_logic import create_roulette, spin_roulette, calculate_win_and_payout
from lexicon.colors import COLOR_MAP, BET_ALL_IN, COLOR_EMOJIS
from services.updates import delete_roulette_message, end_roulette, clear_dicts, delete_user_messages, \
    delete_double_messages, delete_bet_mes

user_message = Router()
user_message.message.filter(IsBotAdminFilter())


@user_message.message(CommandStart())
async def start_command(message: Message, bot: Bot, **data):
    logging.debug('or_f(CommandStart(), IS_NOT_MEMBER >> IS_MEMBER)')
    user_lang = data.get("user_lang", "ru")
    me = await bot.me()
    bot_name = f"@{me.username}"

    text = lexicon.get(user_lang, "welcome", bot_name=bot_name)
    await message.answer(
        f"{text}",
        reply_markup=start_buttons()
    )


@user_message.message(Command('help'))
async def help_command(message: Message, **data):
    user_lang = data.get("user_lang", "ru")

    text = lexicon.get(user_lang, "help_text")
    await message.answer(text, parse_mode="Markdown")


@user_message.message(or_f(Command('profile'), (F.text == 'Профиль')))
async def casino_handler(message: Message, dp_pool: Pool, username, user_id):
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            cursor: Cursor
            await cursor.execute(SELECT_BALANCE, user_id)
            (balance,) = await cursor.fetchone()
            if not balance:
                balance = 0
                logging.error(f"Cannot get {username} {user_id} = BALANCE")
            await cursor.execute(SELECT_DATA_FROM_RESULTS, (user_id,))
            row = await cursor.fetchone()
            if row:
                winCoin, loseCoin, maxWin, maxBet = row

    await message.answer(text=f"{username}: \n"
                              f"Монеты: {balance} 🪙\n"
                              f"Выиграно: {winCoin or 0}\n"
                              f"Проиграно: {loseCoin or 0}\n"
                              f"Макс.выигрыш: {maxWin or 0}\n"
                              f"Макс.ставка: {maxBet or 0}\n")


@user_message.message(or_f(Command('roulette'), (F.text == 'Рулетка')))
async def casino_handler(message: Message, chat_id):
    keyboard = bets_keyboards()
    roulette = await message.answer(
        "<b>🎰 Рулетка</b>\n\n"
        "Угадайте число из:\n\n"
        f"{create_roulette()}\n"
        "Чтобы крутить рулетку, нажмите кнопку или используйте /spin",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    roulette_messages[message.chat.id] = roulette.message_id
    roulette_states[chat_id] = True


@user_message.message((F.text.regexp(r'^\S+\s+на\s+\S+$')))
async def handle_three_word_bet(message: Message, user_id, username, dp_pool: Pool, state: FSMContext, chat_id):
    bet_data = message.text.split()
    logging.debug(bet_data)

    if not roulette_states.get(chat_id, False):
        return

    bet_sum = bet_data[0]
    bet_range_or_color = bet_data[2]

    logging.debug(1)
    if bet_sum.lower().strip() in BET_ALL_IN:
        async with dp_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(SELECT_BALANCE, (user_id,))
                row = await cursor.fetchone()
                if row is None:
                    logging.warning("Недостаточно денег на балансе ")
                    return
                balance = row[0]
                if balance <= 0:
                    warn = await message.answer("Недостаточно денег на балансе ")
                    await asyncio.sleep(5)
                    await message.delete()
                    await warn.delete()
                    return
                bet_sum = int(balance)
    elif not (bet_sum.isdigit() and int(bet_sum) >= 0):
        warn = await message.answer("Сумма ставки должна быть положительным числом.")
        await asyncio.sleep(5)
        await message.delete()
        await warn.delete()
        return
    logging.debug(2)

    color_check = bet_range_or_color.strip().lower().replace('ё', 'е')

    if color_check in COLOR_MAP:
        bet_range_or_color = COLOR_MAP[color_check]

    if not await check_correct_bet(message, bet_range_or_color):
        return

    bet_sum = int(bet_sum)

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
                warn = await message.answer("Недостаточно денег на балансе ")
                await asyncio.sleep(5)
                await message.delete()
                await warn.delete()
                return

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
    bet_message = await message.answer(
        text=f"""Ставка {action}: <a href="tg://user?id={user_id}">{username}</a> {bet_sum} монет на {COLOR_EMOJIS.get(bet_range_or_color, bet_range_or_color)}""",
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


@user_message.message(Command("spin"), GameStates.waiting_for_bet)
async def spin_command_handler(message: Message, bot: Bot, user_id, username, chat_id, dp_pool: Pool,
                               state: FSMContext):
    number, color = spin_roulette()

    await state.update_data(bet_result=(number, color))
    await delete_roulette_message(bot, roulette_messages, chat_id)

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

    await delete_bet_mes(bot)

    clear_dicts()
    await state.clear()

    mes_spin = await message.answer(
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
        "bot_msg": bot_message.message_id
    }

    await asyncio.sleep(3)

    await delete_user_messages(bot)
    await delete_double_messages(bot)

    sorted_lines = sorted(bet_results, key=lambda s: s.split()[0])  # Сортируем список строк
    text_sorted = "\n".join(sorted_lines)

    await message.answer(
        text=f"🎯 Выпал номер: {number} {COLOR_EMOJIS[color]}\n"
             f"{text_sorted}",
        parse_mode="HTML"
    )
    await end_roulette(chat_id=chat_id)
    clear_dicts()


@user_message.message(or_f(Command("balance"), F.text.lower().in_({"баланс", "b", "б"})))
async def show_balance(message: Message, dp_pool, user_id, username):
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            cursor: Cursor
            await cursor.execute(SELECT_BALANCE, user_id)
            (balance,) = await cursor.fetchone()

    await message.answer(
        f"{username}\nМонеты: {balance} {'+ ' + str(total_bet[user_id]) if user_id in total_bet else ''}🪙")


@user_message.message(or_f(F.text.lower() == "/bonus", F.text == "Бонус"))
async def get_daily_bonus(message: Message):
    bonus = await message.answer(
        text="Забрать бонус 🎁",
        reply_markup=bonus_button()
    )
    await asyncio.sleep(20)
    await message.delete()
    await bonus.delete()


# @user_message.message(Command('language'))
# async def language_handle(message: Message):
#     keyboard = choose_lang()
#     await message.answer("Выберите язык / Choose language:", reply_markup=keyboard)
#

@user_message.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def process_user_blocked_bot(event: ChatMemberUpdated, dp_pool: Pool):
    logging.info(f'Пользователь {event.from_user.id} заблокировал бота')
    async with dp_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(UPDATE_USER_ACTIVE, (0, event.from_user.id))


async def check_correct_bet(message: Message, bet_range_or_color):
    # Если диапазон, проверяем его
    if "-" in bet_range_or_color:
        start_end = bet_range_or_color.split("-")
        if len(start_end) != 2 or not all(x.isdigit() for x in start_end):
            await message.answer("Неправильный диапазон чисел.")
            return False
        start, end = map(int, start_end)

        if not (0 <= start < 19 and 0 < end < 19 and start < end):
            await message.answer("Диапазон должен быть в пределах от 1 до 18.")
            return False

    return True
