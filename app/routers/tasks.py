import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, time
from enum import StrEnum, auto
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from sqlmodel import col, select

from app.deps import CurrentUserDep, SessionDep
from app.models import Task, TaskCreate, TaskPublic, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TaskPublic)
async def create_task(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    task: Annotated[TaskCreate, Body()],
) -> Task:
    db_task = Task.model_validate(task, update={"owner_id": current_user.id})
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)
    return db_task


class TaskView(StrEnum):
    TODAY = auto()
    UPCOMMING = auto()
    OVERDUE = auto()


def validate_task_filters(
    completed: Annotated[bool | None, Query()] = None,
    view: Annotated[TaskView | None, Query()] = None,
) -> tuple[bool | None, TaskView | None]:
    if completed is not None and view is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parameters 'completed' and 'view' are mutually exclusive, provide only one or the other",
        )
    return completed, view


@router.get("/", response_model=list[TaskPublic])
async def read_tasks(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    offset: Annotated[
        int,
        Query(
            ge=0,
        ),
    ] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
    filters: Annotated[
        tuple[bool | None, TaskView | None], Depends(validate_task_filters)
    ],
) -> Sequence[Task]:
    query = select(Task).where(Task.owner_id == current_user.id)
    completed, view = filters
    now = datetime.now(UTC)
    # Apply view-specific filters
    if view == TaskView.TODAY:
        today_end = datetime.combine(now.date(), time.max, tzinfo=UTC)
        today_start = datetime.combine(now.date(), time.min, tzinfo=UTC)
        query = query.where(col(Task.due_date).between(today_start, today_end))
    elif view == TaskView.UPCOMMING:
        query = query.where(col(Task.due_date) > now)
    elif view == TaskView.OVERDUE:
        query = query.where(col(Task.due_date) < now)
    # Apply task completion defaults
    if completed is not None:
        # Respect the explicit user fiter
        query = query.where(Task.completed == completed)
    elif view is not None:
        # Default behavior for prespectives when COMPLETED is not explicitly set
        query = query.where(col(Task.completed).is_(False))
    # Apply pagination and ordering
    results = await session.exec(
        query.order_by(col(Task.due_date).asc().nulls_last())
        .offset(offset)
        .limit(limit)
    )
    return results.all()


@router.get("/{task_id}", response_model=TaskPublic)
async def read_task(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    task_id: Annotated[uuid.UUID, Path()],
) -> Task:
    results = await session.exec(
        select(Task).where(Task.id == task_id, Task.owner_id == current_user.id)
    )
    task = results.first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


@router.patch("/{task_id}", response_model=TaskPublic)
async def update_task(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    task_id: Annotated[uuid.UUID, Path()],
    task: Annotated[TaskUpdate, Body()],
) -> Task:
    results = await session.exec(
        select(Task).where(Task.id == task_id, Task.owner_id == current_user.id)
    )
    db_task = results.first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    task_data = task.model_dump(exclude_unset=True)
    db_task.sqlmodel_update(task_data)
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)
    return db_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    task_id: Annotated[uuid.UUID, Path()],
) -> None:
    results = await session.exec(
        select(Task).where(Task.id == task_id, Task.owner_id == current_user.id)
    )
    task = results.first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    await session.delete(task)
    await session.commit()
