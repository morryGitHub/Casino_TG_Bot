from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery


def start_buttons():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Профиль"), KeyboardButton(text="Донат")],
            [KeyboardButton(text="Рулетка"), KeyboardButton(text="Бонус")]
        ],
        resize_keyboard=True
    )
    return keyboard


def bets_keyboards():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1-6", callback_data="bet_500_1-6"),
             InlineKeyboardButton(text="7-12", callback_data="bet_500_7-12"),
             InlineKeyboardButton(text="13-18", callback_data="bet_500_13-18")
             ],
            [InlineKeyboardButton(text="1-9", callback_data="bet_500_1-9"),
             InlineKeyboardButton(text="10-18", callback_data="bet_500_10-18")
             ],
            [InlineKeyboardButton(text="500 на 🟢", callback_data="bet_500_green"),
             InlineKeyboardButton(text="500 на ⚫️", callback_data="bet_500_black"),
             InlineKeyboardButton(text="500 на 🔴", callback_data="bet_500_red")
             ],
            [InlineKeyboardButton(text="Удвоить", callback_data="double"),
             InlineKeyboardButton(text="Отменить", callback_data="cancel"),
             InlineKeyboardButton(text="Крутить", callback_data="spin")
             ]
        ]
    )
    return keyboard


def choose_lang():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Русский 🇷🇺", callback_data='lang_ru'),
            InlineKeyboardButton(text="English 🇬🇧", callback_data='lang_en'),
        ]
    ])
    return keyboard


def bonus_button():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Тык 🐾", callback_data="bonus")]
        ],
    )
    return keyboard
