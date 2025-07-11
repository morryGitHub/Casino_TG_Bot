from aiogram import Bot
from aiogram.types import BotCommand


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота и получить приветствие"),
        BotCommand(command="help", description="Помощь по боту"),
        BotCommand(command="profile", description="Показать ваш профиль и баланс"),
        BotCommand(command="roulette", description="Начать игру рулетка"),
        BotCommand(command="spin", description="Крутить рулетку"),
        BotCommand(command="balance", description="Показать баланс"),
        BotCommand(command="bonus", description="Забрать бонус")
        # BotCommand(command="language", description="Выбрать язык")
    ]
    await bot.set_my_commands(commands)
