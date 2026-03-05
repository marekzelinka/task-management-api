from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUserDep, SessionDep
from app.core.security import hash_password
from app.models import UserCreate, UserPublic
from app.schema import User

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserPublic)
async def create_user(
    *,
    session: SessionDep,
    user: UserCreate,
) -> User:
    duplicate_username_user = await session.scalar(
        select(User).where(User.username.ilike(user.username))
    )
    if duplicate_username_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    duplicate_email_user = await session.scalar(
        select(User).where(User.email.ilike(user.email))
    )
    if duplicate_email_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    db_user = User(
        **user.model_dump(exclude={"email", "password"}),
        email=user.email.lower(),
        hashed_password=hash_password(user.password),
    )

    session.add(db_user)

    await session.commit()
    await session.refresh(db_user)

    return db_user


@router.get("/me", response_model=UserPublic)
async def read_users_me(*, current_user: CurrentUserDep) -> User:
    return current_user
