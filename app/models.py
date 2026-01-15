import uuid
from datetime import UTC, datetime

from pydantic import EmailStr, field_validator
from sqlmodel import Column, DateTime, Field, Relationship, SQLModel


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)
    email: EmailStr = Field(unique=True, index=True)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)

    hashed_password: str

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True), nullable=False, onupdate=lambda: datetime.now(UTC)
        ),
    )

    tasks: list[Task] = Relationship(back_populates="owner", cascade_delete=True)


class UserCreate(UserBase):
    password: str


class UserPublic(UserBase):
    id: uuid.UUID

    created_at: datetime
    updated_at: datetime


class Token(SQLModel):
    access_token: str
    token_type: str


class TaskBase(SQLModel):
    title: str = Field(index=True)
    description: str | None = Field(default=None)
    priority: int = Field(default=1, ge=1, le=5)
    completed: bool = Field(default=False)
    due_date: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), index=True)
    )


class Task(TaskBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True), nullable=False, onupdate=lambda: datetime.now(UTC)
        ),
    )

    owner_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    owner: User = Relationship(back_populates="tasks")


class TaskCreate(TaskBase):
    @field_validator("due_date")
    @classmethod
    def check_due_date_is_future(cls, v: datetime | None) -> datetime | None:
        if v is not None and v < datetime.now(UTC):
            raise ValueError("due_date must be in the future")
        return v


class TaskPublic(TaskBase):
    id: uuid.UUID

    created_at: datetime
    updated_at: datetime

    owner_id: uuid.UUID


class TaskUpdate(SQLModel):
    title: str | None = None
    description: str | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    completed: bool | None = None
    due_date: datetime | None = Field(default=None)
