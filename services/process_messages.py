import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from db.database import bet_messages, user_messages, double_messages, total_bet


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
