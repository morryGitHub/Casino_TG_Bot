import logging

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from db.database import roulette_states, bet_messages, users_bet, total_bet, user_messages, double_messages
from db.queries import SELECT_USER_LANG


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
    logging.debug(f'double_messages => {double_messages}')
    for uid, msg_data in double_messages.items():
        chat_id = msg_data.get("chat_id")
        message_id = msg_data.get("message_id")
        logging.debug(f'chat_id => {chat_id}')
        logging.debug(f'message_id => {message_id}')

        if chat_id and message_id:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                logging.warning(f"Ошибка при удалении double-ставки у {uid}: {e}")
    double_messages.clear()
