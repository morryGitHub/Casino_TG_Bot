from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiomysql import Pool

from filters.CheckBalance import CheckBalance
from filters.ValidMessageFilter import ValidMessageFilter
from lexicon.colors import COLOR_EMOJIS

from FSM.FSM import GameStates
from db.database import bet_messages, roulette_messages, users_bet, total_bet
from services.database_functions import check_and_get_valid_bet, update_balance_before_spin, handle_double_bet, \
    update_balance_after_spin, update_balance_after_bonus, update_user_lang
from services.roulette_logic import add_or_update_user_bet
from services.updates import clear_dicts, delete_double_messages, delete_bet_mes, \
    edit_double_messages, is_bet_ready, process_spin_round

user_callback = Router()


@user_callback.callback_query(ValidMessageFilter(roulette_messages), (F.data.startswith("bet_")), CheckBalance())
async def bet_handler(callback: CallbackQuery, state: FSMContext, username, dp_pool: Pool, user_id):
    await callback.answer()
    bet_data = callback.data.split("_")
    bet_sum = int(bet_data[1])  # 500, преобразуем в int
    bet_range_or_color = bet_data[2]  # например, "1-18"

    if not await check_and_get_valid_bet(callback.message, dp_pool, user_id, bet_sum=bet_sum):
        await callback.answer("Недостаточно денег на балансе", show_alert=True)
        return

    # Если пользователь уже ставил, добавляем новую ставку в список
    action = add_or_update_user_bet(user_id, bet_sum, bet_range_or_color, username)

    if action == "принята":
        await state.set_state(GameStates.waiting_for_bet)

    # Отправляем сообщение
    bet_message = await callback.message.answer(
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


@user_callback.callback_query(ValidMessageFilter(roulette_messages), (F.data == 'spin'), GameStates.waiting_for_bet)
async def spin_handler(callback: CallbackQuery, bot: Bot, state: FSMContext, dp_pool: Pool, username, user_id, chat_id):
    await callback.answer()
    await process_spin_round(
        user_id=user_id,
        username=username,
        chat_id=chat_id,
        bot=bot,
        state=state,
        dp_pool=dp_pool,
        trigger_message=callback.message,
        is_callback=True
    )


@user_callback.callback_query(ValidMessageFilter(roulette_messages), F.data == 'spin')
async def spin_wrong_state(callback: CallbackQuery):
    await callback.answer("Сначала сделайте ставку!")


@user_callback.callback_query(ValidMessageFilter(roulette_messages), F.data == 'double')
async def double_bet(callback: CallbackQuery, bot: Bot, dp_pool: Pool, user_id, username):
    if not await is_bet_ready(callback, user_id):
        return

    bets_text = f"{username} удвоил все свои ставки:\n"
    new_total = sum(bet[0] for bet in users_bet[user_id])  # сумма текущих ставок
    double_sum = new_total  # столько нужно списать с баланса
    await handle_double_bet(callback, dp_pool, user_id, double_sum)

    # Формируем красивый ответ
    bets_text += "\n".join(
        [f"💰 {b[0]} на {COLOR_EMOJIS.get(b[1], b[1])}" for b in users_bet[user_id]]
    )

    await edit_double_messages(callback, bot, user_id, bets_text)


@user_callback.callback_query(ValidMessageFilter(roulette_messages), F.data == 'cancel')
async def spin_wrong_state(callback: CallbackQuery, bot: Bot, state: FSMContext, username, user_id, dp_pool: Pool):
    if not await is_bet_ready(callback, user_id):
        return

    await delete_bet_mes(bot)
    await delete_double_messages(bot)
    await state.clear()

    total = total_bet[user_id]
    await callback.answer(f"{username} ваши ставки были отменены")
    await update_balance_after_spin(dp_pool, total, user_id)
    clear_dicts()


@user_callback.callback_query(F.data == "bonus")
async def process_bonus(callback: CallbackQuery, dp_pool: Pool, user_id):
    await update_balance_after_bonus(callback, dp_pool, user_id)


@user_callback.callback_query(F.data.startswith("lang_"))
async def process_language_choice(callback: CallbackQuery, state: FSMContext, dp_pool: Pool, user_id):
    lang_code = callback.data.split('_')[1]

    await update_user_lang(dp_pool, lang_code, user_id)
    await state.update_data(language=lang_code)
    await callback.answer(f"Язык установлен: {lang_code.upper()}")
    await callback.message.answer(f"Выбран язык: {lang_code.upper()}")
    await callback.message.delete()
