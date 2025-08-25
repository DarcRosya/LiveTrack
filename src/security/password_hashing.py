from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

# Argon2 теперь основной, bcrypt - для проверки старых хэшей
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Ваши функции hash_password и verify_password остаются БЕЗ ИЗМЕНЕНИЙ!
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)