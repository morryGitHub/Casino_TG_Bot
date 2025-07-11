from random import randint

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
        result += '  '.join(row) + '\n'
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
                if span == 6:
                    return True, amount * 3
                elif span == 9:
                    return True, amount * 2
                else:
                    return True, amount  # Просто возврат (или как ты хочешь)
        except ValueError:
            return False, 0
    return False, 0
