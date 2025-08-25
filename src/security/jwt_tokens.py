from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from pydantic import SecretStr

from src.models.user import User
from src.config.settings import settings


TOKEN_TYPE_FIELD = "type"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
EMAIL_TOKEN_TYPE = "email"


###### CREATE SECTION ######
def create_access_token(user: User) -> str:
    jwt_payload = {
        "sub": str(user.id),
        "username": user.username,
        "email": user.email,
    }
    return create_jwt(
        token_type=ACCESS_TOKEN_TYPE,
        token_data=jwt_payload,
        expire_minutes=settings.auth.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


def create_refresh_token(user: User) -> str:
    jwt_payload = {
        "sub": str(user.id), 
    }
    return create_jwt(
        token_type=REFRESH_TOKEN_TYPE, 
        token_data=jwt_payload,
        expire_timedelta=timedelta(days=settings.auth.REFRESH_TOKEN_EXPIRE_DAYS),
    )


# def create_email_token(user: User) -> str:
#     jwt_payload = {
#         "sub": user.email
#     }
#     return create_jwt(
#         token_type=EMAIL_TOKEN_TYPE,
#         token_data=jwt_payload,
#         expire_minutes=settings.auth.EMAIL_TOKEN_EXPIRE_MINUTES, 
#     )


def create_jwt(
    token_type: str,
    token_data: dict,
    expire_minutes: int = settings.auth.ACCESS_TOKEN_EXPIRE_MINUTES,
    expire_timedelta: timedelta | None = None, 
) -> str:
    jwt_payload = {TOKEN_TYPE_FIELD: token_type}
    jwt_payload.update(token_data)
    return encode_jwt(
        payload=jwt_payload,
        expire_minutes=expire_minutes,
        expire_timedelta=expire_timedelta
    )


###### ENCODE/DECODE SECTION ######
def encode_jwt(
    payload: dict, 
    private_key: SecretStr = settings.auth.SECRET_KEY,
    algorithm: str = settings.auth.ALGORITHM,
    expire_minutes: int = settings.auth.ACCESS_TOKEN_EXPIRE_MINUTES,
    expire_timedelta: timedelta | None = None,
) -> str:
    to_encode = payload.copy()
    now = datetime.now(timezone.utc)

    if expire_timedelta:
        expire = now + expire_timedelta
    elif expire_minutes:
        expire = now + timedelta(minutes=expire_minutes)
    else:
        expire = now + timedelta(minutes=15)

    to_encode.update(
        exp=expire,
        iat=now,
        # jti=str(uuid.uuid4()),
    )
    return jwt.encode(to_encode, private_key.get_secret_value(), algorithm=algorithm)


def decode_jwt(
    token: str | bytes,
    private_key: SecretStr = settings.auth.SECRET_KEY,
    algorithm: str = settings.auth.ALGORITHM,
) -> dict:
    try:
        return jwt.decode(
            token,
            private_key.get_secret_value(),
            algorithms=[algorithm],
        )
    except (jwt.InvalidTokenError, jwt.PyJWTError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid credentials"
        )