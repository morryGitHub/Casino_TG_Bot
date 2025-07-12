import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiomysql import Pool

from db.database import roulette_states, bet_messages, users_bet, total_bet, user_messages, double_messages, \
    roulette_messages
from lexicon.colors import COLOR_EMOJIS
from services.roulette_logic import spin_roulette, finalize_round


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


async def delete_roulette_message(bot, roulette_messages, chat_id):
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


async def delete_bet_mes(bot: Bot):
    for uid, msgs in bet_messages.items():
        for msg in msgs:
            try:
                await bot.delete_message(
                    chat_id=msg["chat_id"],
                    message_id=msg["message_id"]
                )
            except Exception as e:
                logging.warning(f"Не удалось удалить сообщение ставки у {uid}: {e}")


async def delete_user_messages(bot: Bot):
    for uid, msg_data in user_messages.items():
        chat_id = msg_data.get("chat_id")

        bot_msg_id = msg_data.get("bot_msg")
        if chat_id and bot_msg_id:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=bot_msg_id)
            except Exception as e:
                logging.warning(f"Ошибка при удалении текстового сообщения у {uid}: {e}")

        user_msg_id = msg_data.get("user_msg")
        if chat_id and user_msg_id:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=user_msg_id)
            except Exception as e:
                logging.warning(f"Ошибка при удалении анимации у {uid}: {e}")


async def delete_double_messages(bot: Bot):
    for uid, msg_data in double_messages.items():
        chat_id = msg_data.get("chat_id")
        message_id = msg_data.get("message_id")

        if chat_id and message_id:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                logging.warning(f"Ошибка при удалении double-ставки у {uid}: {e}")
    double_messages.clear()


async def edit_double_messages(callback: CallbackQuery, bot: Bot, user_id: int, bets_text: str):
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
        await delete_roulette_message(bot, roulette_messages, chat_id)

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
