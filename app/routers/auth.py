from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from app.core.security import create_access_token, hash_password, verify_password
from app.deps import CurrentUserDep, SessionDep
from app.models import Token, User, UserCreate, UserPublic

router = APIRouter(tags=["auth"])


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserPublic
)
async def register_user(
    *,
    session: SessionDep,
    user: Annotated[UserCreate, Body()],
) -> User:
    results = await session.exec(select(User).where(User.username == user.username))
    db_user = results.first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    hashed_password = hash_password(user.password)
    user_dict = user.model_dump()
    new_user = User.model_validate(
        user_dict, update={"hashed_password": hashed_password}
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return new_user


@router.post("/token", status_code=status.HTTP_200_OK, response_model=Token)
async def login_for_access_token(
    *,
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    results = await session.exec(
        select(User).where(User.username == form_data.username)
    )
    user = results.first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})

    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me", response_model=UserPublic)
async def read_users_me(*, current_user: CurrentUserDep) -> User:
    return current_user
