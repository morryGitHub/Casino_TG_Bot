LEXICON_RU = {
    "welcome": "👋 Добро пожаловать в {bot_name}.",
    "help_text": (
        "🎰 Добро пожаловать в CatCasino — самое мяу-казино в Telegram! 🐾\n\n"
        "Доступные команды:\n"
        "/start — Начать игру и познакомиться с котиками\n"
        "/help — Показать подсказки (если запутался)\n"
        "/profile — Посмотреть свой кошелёк и статистику\n"
        "/roulette — Играть в рулетку с пушистыми шансами\n"
        "/spin — Крутить рулетку и ловить удачу\n"
        "/balance — Проверить баланс монеток\n\n"
        "Как ставить:\n"
        "💰 Напиши `<сумма> на <число или цвет>`\n"
        "Пример: `1000 на 7` или `500 на красный`\n\n"
        "Каждые 24 часа доступен бонус чтобы пополнить монетки\n"
        "🐱 Минимальная ставка — 500 монеток.\n"
        "Пусть котики приносят тебе удачу и большие выигрыши! 🍀😸"
    ),
    "profile_text": (
        "{username}:\n"
        "Монеты: {balance} 🪙\n"
        "Выиграно: \n"
        "Проиграно: \n"
        "Макс.выигрыш: \n"
        "Макс.ставка: \n"
    ),
    "roulette_start": (
        "<b>🎰 Рулетка</b>\n\n"
        "Угадайте число из:\n\n"
        "{roulette_numbers}\n"
        "Чтобы крутить рулетку, нажмите кнопку или используйте /spin"
    ),
    "bet_placed": (
        "Ставка {action}: <a href=\"tg://user?id={user_id}\">{username}</a> "
        "{bet_sum} монет на {bet_range_or_color}"
    ),
    "not_enough_balance": "Недостаточно денег на балансе",
    "spin_wait": "<a href=\"tg://user?id={user_id}\">{username}</a> крутит...(3 сек)",
    "spin_result": (
        "🎯 Выпал номер: {number} {color_emoji}\n"
        "{bet_results}"
    ),
    "balance_text": (
        "{username}\n"
        "Монеты: {balance}{extra}🪙"
    ),
    "min_bet_error": "Сумма ставки должна быть положительным числом больше 500.",
    "invalid_range": "Диапазон должен быть в пределах от 1 до 18.",
    "invalid_bet_format": "Неправильный формат ставки. Используйте: <сумма> на <число или цвет>.",
    "old_button": "Эта кнопка устарела и недействительна.",
    "make_bet_first": "Сначала сделайте ставку",
    "error_user_not_found": "Ошибка: пользователь не найден в БД.",
    "error_db": "Ошибка работы с базой данных.",
    "error_general": "Произошла ошибка.",
    "bet_increased": "увеличена",
    "bet_accepted": "принята"
}

LEXICON_EN = {
    "welcome": "👋 Welcome to {bot_name}.",
    "help_text": (
        "🎰 Welcome to CatCasino — the purr-fect casino in Telegram! 🐾\n\n"
        "Available commands:\n"
        "/start — Start playing and meet the kitties\n"
        "/help — Show tips (if you get lost)\n"
        "/profile — View your wallet and stats\n"
        "/roulette — Play roulette with furry odds\n"
        "/spin — Spin the roulette and catch your luck\n"
        "/balance — Check your coin balance\n\n"
        "How to bet:\n"
        "💰 Type `<amount> on <number or color>`\n"
        "Example: `1000 on 7` or `500 on red`\n\n"
        "🐱 Minimum bet is 500 coins.\n"
        "May the kitties bring you luck and big wins! 🍀😸"
    ),
    "profile_text": (
        "{username}:\n"
        "Coins: {balance} 🪙\n"
        "Won: \n"
        "Lost: \n"
        "Max win: \n"
        "Max bet: \n"
    ),
    "roulette_start": (
        "<b>🎰 Roulette</b>\n\n"
        "Guess a number from:\n\n"
        "{roulette_numbers}\n"
        "To spin the roulette, press a button or use /spin"
    ),
    "bet_placed": (
        "Bet {action}: <a href=\"tg://user?id={user_id}\">{username}</a> "
        "{bet_sum} coins on {bet_range_or_color}"
    ),
    "not_enough_balance": "Not enough balance",
    "spin_wait": "<a href=\"tg://user?id={user_id}\">{username}</a> is spinning...(3 sec)",
    "spin_result": (
        "🎯 Number landed on: {number} {color_emoji}\n"
        "{bet_results}"
    ),
    "balance_text": (
        "{username}\n"
        "Coins: {balance}{extra}🪙"
    ),
    "min_bet_error": "Bet amount must be a positive number greater than 500.",
    "invalid_range": "Range must be between 1 and 18.",
    "invalid_bet_format": "Invalid bet format. Use: <amount> on <number or color>.",
    "old_button": "This button is outdated and invalid.",
    "make_bet_first": "Please make a bet first",
    "error_user_not_found": "Error: user not found in DB.",
    "error_db": "Database error.",
    "error_general": "An error occurred.",
    "bet_increased": "increased",
    "bet_accepted": "accepted"
}
