import asyncio
import logging
import math

from random import randint
from services.database_functions import update_balance_after_spin, update_statistics
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiomysql import Pool

from db.database import roulette_states, bet_messages, users_bet, total_bet, user_messages, roulette_messages
from lexicon.colors import COLOR_EMOJIS
from services.process_messages import delete_bet_mes, delete_user_messages, delete_double_messages

mono_digits = {
    '0': '\U0001D7F6',
    '1': '\U0001D7F7',
    '2': '\U0001D7F8',
    '3': '\U0001D7F9',
    '4': '\U0001D7FA',
    '5': '\U0001D7FB',
    '6': '\U0001D7FC',
    '7': '\U0001D7FD',
    '8': '\U0001D7FE',
    '9': '\U0001D7FF',
}


def to_mono_number(number: int) -> str:
    # Преобразуем число в строку моноширинными цифрами, без ведущих нулей
    return ''.join(mono_digits[d] for d in str(number))


def create_roulette():
    colors = ['🔴', '⚫️', '🟢']
    lines = []

    for i in range(19):
        if i == 0:
            # Для 0 используем моноширинный ноль
            lines.append(f"{to_mono_number(i)} {colors[2]}")
            continue
        color = colors[0] if i % 2 == 0 else colors[1]
        lines.append(f"{to_mono_number(i):{to_mono_number(0)}>2} {color}")

    # Разбиваем на строки по 6 элементов
    rows = [lines[i:i + 6] for i in range(1, len(lines), 6)]
    result = f"{lines[0]}\n"  # 0 🟢
    for row in rows:
        result += ' '.join(row) + '\n'
    return result


def spin_roulette():
    number = randint(0, 18)
    if number == 0:
        color = 'green'
    elif number % 2 == 0:
        color = 'red'
    else:
        color = 'black'
    return [number, color]


def calculate_win_and_payout(number: int, color: str, bet_choice: str, amount: int) -> tuple[bool, int]:
    """
    Проверяет, выиграл ли пользователь, и рассчитывает выплату.

    :param number: Выпавшее число (0-36)
    :param color: Цвет сектора (🔴, ⚫️, 🟢)
    :param bet_choice: Что поставил пользователь (цвет или диапазон)
    :param amount: Сумма ставки
    :return: (победа: bool, выплата: int)
    """
    RED_VARIANTS = {"red", "красное", "красный", "к", "красн"}
    BLACK_VARIANTS = {"black", "чёрное", "черное", "чёрный", "черный", "ч"}
    GREEN_VARIANTS = {"green", "зеленое", "зелёное", "зелёный", "зеленый", "з", "зел"}

    if bet_choice in RED_VARIANTS:
        if color == "red":
            return True, amount * 2
    elif bet_choice in BLACK_VARIANTS:
        if color == "black":
            return True, amount * 2
    elif bet_choice in GREEN_VARIANTS:
        if number == 0:
            return True, amount * 18
    elif "-" in bet_choice:
        try:
            start, end = map(int, bet_choice.split("-"))
            if start <= number <= end:
                span = (end + 1) - start  # Кол-во чисел в диапазоне
                return True, math.ceil(amount * (18 / span))
        except ValueError:
            return False, 0
    return False, 0


async def process_all_bets(number: int, color: str, dp_pool: Pool) -> tuple[list[str], int, int]:
    """Обрабатывает все ставки, возвращает сообщения о ставках, общую сумму ставок и выплат."""
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
                    f"💲 <a href='tg://user?id={uid}'>{username}</a> выиграл {payout} на {COLOR_EMOJIS.get(target, target)}"
                )

                await update_balance_after_spin(dp_pool, payout, uid)

            bet_results.append(f"🐾 {username} {amount} на {COLOR_EMOJIS.get(target, target)}")

    return bet_results, total_bet_sum, total_payout_sum


async def finalize_round(bot: Bot, state: FSMContext, user_id: int, number: int, color: str, dp_pool: Pool):
    """Финальный этап раунда: обработка ставок, обновление статистики, очистка состояния."""
    bet_results, total_bet_sum, total_payout_sum = await process_all_bets(number, color, dp_pool)
    await update_statistics(user_id, total_bet_sum, total_payout_sum, dp_pool)
    await delete_bet_mes(bot)
    clear_dicts()
    await state.clear()
    return bet_results


def add_or_update_user_bet(user_id: int, bet_sum: int, bet_range_or_color: str, username: str) -> str:
    """
    Добавляет или обновляет ставку пользователя.
    Возвращает строку действия: "принята" или "увеличена".
    """
    if user_id in users_bet:
        for bet in users_bet[user_id]:
            if bet[1] == bet_range_or_color:
                bet[0] += bet_sum
                total_bet[user_id] += bet_sum
                return "увеличена"
        users_bet[user_id].append([bet_sum, bet_range_or_color, username])
        total_bet[user_id] += bet_sum
        return "принята"
    else:
        users_bet[user_id] = [[bet_sum, bet_range_or_color, username]]
        total_bet[user_id] = bet_sum
        return "принята"


async def process_last_update(bot: Bot):
    updates = await bot.get_updates(limit=10)

    if not updates:
        return

    last_update = updates[-1]

    if last_update.message:
        chat_id = last_update.message.chat.id
        text = last_update.message.text

        await bot.send_message(
            chat_id=chat_id,
            text=f"🔁 Бот снова в сети!\nВы писали: {text}"
        )
    await bot.delete_webhook(drop_pending_updates=True)


async def delete_roulette_message(bot, chat_id):
    message_id = roulette_messages.get(chat_id)
    if message_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
            roulette_messages.pop(chat_id, None)
        except Exception as e:
            logging.warning(f"Ошибка при удалении рулетки: {e}")


async def end_roulette(chat_id: int):
    roulette_states[chat_id] = False


def clear_dicts():
    bet_messages.clear()
    users_bet.clear()
    total_bet.clear()
    user_messages.clear()


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


async def is_bet_ready(callback: CallbackQuery, user_id: int):
    if user_id not in users_bet or not users_bet[user_id]:
        await callback.answer("Сначала сделайте ставку")
        return False
    return True


async def process_spin_round(
        user_id: int,
        username: str,
        chat_id: int,
        bot: Bot,
        state: FSMContext,
        dp_pool: Pool,
        trigger_message: Message,
        is_callback: bool = False
):
    number, color = spin_roulette()
    await state.update_data(bet_result=(number, color))

    if is_callback:
        await trigger_message.delete()
    else:
        await delete_roulette_message(bot, chat_id)

    bet_results = await finalize_round(bot, state, user_id, number, color, dp_pool)

    mes_spin = await trigger_message.answer(
        f'<a href="tg://user?id={user_id}">{username}</a> крутит...(3 сек)',
        parse_mode="HTML"
    )

    bot_message = await bot.send_animation(
        chat_id=chat_id,
        animation='CgACAgQAAxkBAAIBTWhhY9tM5QKXejsi-QvzHNXRXgLMAALVAgACuiENU9OiouXPz52yNgQ'
    )

    user_messages[user_id] = {
        "chat_id": chat_id,
        "user_msg": mes_spin.message_id,
        "bot_msg": bot_message.message_id,
    }

    await asyncio.sleep(3)
    await delete_user_messages(bot)
    await delete_double_messages(bot)

    sorted_lines = sorted(bet_results, key=lambda s: s.split()[0])
    text_sorted = "\n".join(sorted_lines)

    await trigger_message.answer(
        text=f"🎯 Выпал номер: {number} {COLOR_EMOJIS[color]}\n{text_sorted}",
        parse_mode="HTML"
    )

    await end_roulette(chat_id=chat_id)
    clear_dicts()
