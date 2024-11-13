def country_code_to_flag(country_code: str) -> str:
        # Преобразуем код страны (например, 'EE') в эмодзи флага
        return ''.join([chr(0x1F1E6 + ord(c) - ord('A')) for c in country_code.upper()])