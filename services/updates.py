from aiogram import Bot


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
