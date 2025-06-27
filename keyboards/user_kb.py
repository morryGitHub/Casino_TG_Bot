from aiogram import Bot
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup,CallbackQuery


def set_main_menu(bot: Bot):
    pass


def start_buttons():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Профиль"), KeyboardButton(text="Магазин")],
            [KeyboardButton(text="Другие боты"), KeyboardButton(text="Донат")]
        ],
        resize_keyboard=True
    )
    return keyboard


def bets_keyboards():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1 - 6", callback_data="bet"),
             InlineKeyboardButton(text="7-12", callback_data="bet"),
             InlineKeyboardButton(text="13-18", callback_data="bet")
             ],
            [InlineKeyboardButton(text="1 - 9", callback_data="bet"),
             InlineKeyboardButton(text="10 - 18", callback_data="bet")
             ],
            [InlineKeyboardButton(text="500 на 🟢", callback_data="bet"),
             InlineKeyboardButton(text="500 на ⚫️", callback_data="bet"),
             InlineKeyboardButton(text="500 на 🔴", callback_data="bet")
             ],
            [InlineKeyboardButton(text="Удвоить", callback_data="double"),
             InlineKeyboardButton(text="Повторить", callback_data="rebet"),
             InlineKeyboardButton(text="Крутить", callback_data="spin")
             ]
        ]
    )
    return keyboard
