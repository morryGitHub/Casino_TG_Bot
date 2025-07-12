import asyncio

from aiogram import Bot, Router, F
from aiogram.filters import CommandStart, Command, or_f, ChatMemberUpdatedFilter, KICKED
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ChatMemberUpdated
from aiomysql import Pool

from FSM.FSM import GameStates
from db.database import roulette_messages, bet_messages, roulette_states, total_bet
from filters.CheckChatMember import IsBotAdminFilter
from keyboards.user_kb import start_buttons, bets_keyboards, bonus_button
from lexicon.Lexicon import lexicon
from services.database_functions import check_and_get_valid_bet, update_balance_before_spin, update_user_active, \
    get_balance_data, get_balance
from services.roulette_logic import create_roulette, add_or_update_user_bet, check_correct_bet, process_spin_round
from lexicon.colors import COLOR_MAP, COLOR_EMOJIS

user_message = Router()
user_message.message.filter(IsBotAdminFilter())


@user_message.message(CommandStart())
async def start_command(message: Message, bot: Bot, **data):
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
    balance, winCoin, loseCoin, maxWin, maxBet = await get_balance_data(dp_pool, username, user_id)
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

    if not roulette_states.get(chat_id, False):
        return

    your_bet = bet_data[0]
    bet_range_or_color = bet_data[2]

    bet_sum = await check_and_get_valid_bet(message, dp_pool, user_id, min_balance=50, bet_sum=your_bet)

    if bet_sum is None:
        return  # недостаточно средств, сообщение уже отправлено

    color_check = bet_range_or_color.strip().lower().replace('ё', 'е')

    if color_check in COLOR_MAP:
        bet_range_or_color = COLOR_MAP[color_check]

    if not await check_correct_bet(message, bet_range_or_color):
        return

    bet_sum = int(bet_sum)
    # Если пользователь уже ставил, добавляем новую ставку в список
    action = add_or_update_user_bet(user_id, bet_sum, bet_range_or_color, username)

    if action == "принята":
        await state.set_state(GameStates.waiting_for_bet)

    # Отправляем сообщение
    bet_message = await message.answer(
        text=f"""Ставка {action}: <a href="tg://user?id={user_id}">{username}</a> {bet_sum} монет на {COLOR_EMOJIS.get(bet_range_or_color, bet_range_or_color)}""",
        parse_mode="HTML"
    )

    await update_balance_before_spin(dp_pool, bet_sum, user_id)

    if user_id not in bet_messages:
        bet_messages[user_id] = []

    bet_messages[user_id].append({
        "chat_id": bet_message.chat.id,
        "message_id": bet_message.message_id
    })


@user_message.message(Command("spin"), GameStates.waiting_for_bet)
async def spin_command_handler(message: Message, bot: Bot, user_id, username, chat_id, dp_pool: Pool,
                               state: FSMContext):
    await process_spin_round(
        user_id=user_id,
        username=username,
        chat_id=chat_id,
        bot=bot,
        state=state,
        dp_pool=dp_pool,
        trigger_message=message
    )


@user_message.message(or_f(Command("balance"), F.text.lower().in_({"баланс", "b", "б"})))
async def show_balance(message: Message, dp_pool, user_id, username):
    balance = await get_balance(dp_pool, user_id)
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
    await update_user_active(dp_pool, event)
