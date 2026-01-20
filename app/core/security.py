from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import config

password_hash = PasswordHash.recommended()


ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=config.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.secret_key, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, config.secret_key, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None

        return username
    except jwt.PyJWTError:
        return None
