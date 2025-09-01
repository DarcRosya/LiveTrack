import re

# Наше "супер-правило" для пароля
PASSWORD_REGEX = r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?!.*\s).{8,}$"

def is_password_strong_enough(password: str) -> bool:
    if not password or not re.match(PASSWORD_REGEX, password):
        return False
    return True
