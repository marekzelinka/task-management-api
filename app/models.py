from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field


def check_hex_color(color: str | None) -> str | None:
    if color is None:
        return None
    if not re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", color):
        raise ValueError("color must be in hex format (e.g., #fff or #ffffff)")
    return color.lower()


HexColor = Annotated[
    str, Field(examples=["#fff", "#ffffff"]), AfterValidator(check_hex_color)
]


def check_due_date_is_future(due_date: datetime) -> datetime:
    if due_date < datetime.now(tz=UTC):
        raise ValueError("date must be in the future")
    return due_date


DueDate = Annotated[datetime, AfterValidator(check_due_date_is_future)]


class Paged[SchemaType](BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    page: int
    per_page: int
    total: int
    results: list[SchemaType]


class PaginationParams(BaseModel):
    page: Annotated[int, Field(ge=1)] = 1
    per_page: Annotated[int, Field(ge=1, le=100)] = 10

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        return self.per_page


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserPublic(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class Token(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str


class ProjectCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=255)]
    color: HexColor | None = None


class ProjectUpdate(BaseModel):
    title: Annotated[str | None, Field(max_length=255)] = None
    color: HexColor | None = None


class ProjectPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    color: str | None
    created_at: datetime


class TaskBase(BaseModel):
    description: Annotated[str | None, Field(max_length=500)] = None
    due_date: DueDate | None = None
    project_id: int | None = None


class TaskCreate(TaskBase):
    title: Annotated[str, Field(min_length=1, max_length=255)]
    priority: Annotated[int, Field(ge=1, le=5)] = 1
    completed: bool = False


class TaskUpdate(TaskBase):
    title: Annotated[str | None, Field(max_length=255)] = None
    priority: Annotated[int | None, Field(ge=1, le=5)] = None
    completed: bool | None = None


class TaskPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    priority: Annotated[int, Field(ge=1, le=5)]
    completed: bool
    due_date: datetime | None
    project_id: int | None


class TaskPublicWithProject(TaskPublic):
    project: ProjectPublic | None = None


class TaskPublicWithLabels(TaskPublic):
    labels: list[LabelPublic] = []


class TaskPublicWithProjectLabels(TaskPublicWithProject, TaskPublicWithLabels):
    pass


class LabelBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=50)]
    color: HexColor | None = None


class LabelCreate(LabelBase):
    pass


class LabelUpdate(BaseModel):
    name: Annotated[str | None, Field(max_length=50)] = None
    color: HexColor | None = None


class LabelPublic(LabelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class LabelPublicWithTasks(LabelPublic):
    tasks: list[TaskPublic] = []
