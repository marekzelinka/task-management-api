from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import SessionDep
from app.core.limiter import limiter
from app.core.security import create_access_token, verify_password
from app.models import Token
from app.schema import User

router = APIRouter(tags=["auth"])


@router.post("/token", status_code=status.HTTP_200_OK, response_model=Token)
@limiter.limit("10/minute")
async def login_for_access_token(
    *,
    request: Request,  # pyrefly:ignore[unused-parameter]  # noqa: ARG001
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = await session.scalar(
        select(User).where(User.username.ilike(form_data.username))
    )
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})

    return Token(access_token=access_token, token_type="bearer")
