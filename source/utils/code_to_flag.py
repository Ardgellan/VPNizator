def country_code_to_flag(country_code: str) -> str:
    # Защита от пустого кода
    if not country_code:
        return ""

    code = country_code.upper()

    # Если код ENC — возвращаем глобус
    if code == "ENC":
        return "🌐"

    # Иначе работаем как раньше (генерируем флаг из букв)
    return ''.join([chr(0x1F1E6 + ord(c) - ord('A')) for c in code])