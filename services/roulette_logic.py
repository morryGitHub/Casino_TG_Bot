from random import randint


def create_roulette():
    colors = ['🔴', '⚫️', '🟢']
    lines = []

    for i in range(19):
        if i == 0:
            lines.append(f"{i:02} {colors[2]}")
            continue
        color = colors[0] if i % 2 == 0 else colors[1]
        lines.append(f"{i:02} {color}")

    # Разбиваем на строки по 6 элементов
    rows = [lines[i:i + 6] for i in range(1, len(lines), 6)]
    result = f"{lines[0]}\n"  # 0 🟢
    for row in rows:
        result += '   '.join(row) + '\n'
    return result


def spin_roulette():
    number = randint(0, 36)
    if number == 0:
        color = '🟢'
    elif number % 2 == 0:
        color = '🔴'
    else:
        color = '⚫️'
    return [number, color]
