from aiogram import Bot, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from keyboards.user_kb import start_buttons, bets_keyboards
from database.data import users_balance
from services.roulette_logic import create_roulette, spin_roulette

user = Router()


@user.message(CommandStart())
async def start_command(message: Message, bot: Bot):
    me = await bot.me()
    username = f"@{me.username}"
    user_id = message.from_user.id

    if user_id not in users_balance:
        users_balance[user_id] = 2000

    await message.answer(
        f"👋 Добро пожаловать в {username}.",
        reply_markup=start_buttons()
    )


@user.message(Command('help'))
async def help_command(message: Message):
    await message.answer(
        "..."
    )


@user.message(Command('profile'))
async def casino_handler(message: Message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    if not name:
        name = message.from_user.username
    await message.answer(text=f"{name}: \n"
                              f"Монеты: {users_balance[user_id]}\n"
                              f"Выиграно: \n"
                              f"Проиграно: \n"
                              f"Макс.выигрыш: \n"
                              f"Макс.ставка: \n")


@user.message(Command('roulette'))
async def casino_handler(message: Message):
    keyboard = bets_keyboards()
    await message.answer(
        "<b>🎰 Рулетка</b>\n\n"
        "Угадайте число из:\n\n"
        f"{create_roulette()}\n"
        "Чтобы крутить рулетку, нажмите кнопку или используйте /spin",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@user.callback_query(F.data == 'spin')
async def spin_handler(callback: CallbackQuery):
    number, color = spin_roulette()
    await callback.answer(f"🎯 Выпал номер: {number} {color}")
    await callback.message.answer(f"🎯 Выпал номер: {number} {color}")


@user.message(Command("spin"))
async def spin_command_handler(message: Message):
    number, color = spin_roulette()
    user_id = message.from_user.id
    username = message.from_user.first_name
    await message.answer(
        f'<a href="tg://user?id={user_id}">{username}</a>',
        parse_mode="HTML"
    )
    await message.answer(f"🎯 Выпал номер: {number} {color}")
