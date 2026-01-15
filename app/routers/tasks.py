import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, time
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Query, status
from sqlmodel import col, select

from app.deps import CurrentUserDep, SessionDep
from app.models import (
    Project,
    Task,
    TaskCreate,
    TaskPublic,
    TaskPublicWithProject,
    TaskUpdate,
)

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


@router.post(
    "/{task_id}/duplicate",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskPublic,
)
async def create_task_copy(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    task_id: Annotated[uuid.UUID, Path()],
) -> Task:
    results = await session.exec(
        select(Task).where(Task.id == task_id, Task.owner_id == current_user.id)
    )
    db_task = results.first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    task_data = db_task.model_dump(
        exclude={"id", "completed", "created_at", "updated_at"}
    )
    new_task = Task.model_validate(
        task_data, update={"title": f"{task_data['title']} (Copy)"}
    )
    session.add(new_task)
    await session.commit()
    await session.refresh(new_task)
    return new_task


@router.get("/", response_model=list[TaskPublic])
async def read_tasks(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
    completed: Annotated[bool | None, Query()] = None,
    priority: Annotated[int | None, Query(ge=1, le=5)] = None,
) -> Sequence[Task]:
    query = select(Task).where(Task.owner_id == current_user.id)
    if completed is not None:
        query = query.where(Task.completed == completed)
    if priority is not None:
        query = query.where(Task.priority == priority)
    results = await session.exec(query.offset(offset).limit(limit))
    return results.all()


@router.get("/upcomming", response_model=list[TaskPublic])
async def read_upcomming_tasks(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
    priority: Annotated[int | None, Query(ge=1, le=5)] = None,
) -> Sequence[Task]:
    now = datetime.now(UTC)
    query = (
        select(Task)
        .where(Task.owner_id == current_user.id)
        .where(col(Task.due_date) > now)
        .where(col(Task.completed).is_(False))
    )
    if priority is not None:
        query = query.where(Task.priority == priority)
    results = await session.exec(
        query.order_by(col(Task.due_date).asc().nulls_last())
        .offset(offset)
        .limit(limit)
    )

    return results.all()


@router.get("/today", response_model=list[TaskPublic])
async def read_due_today_tasks(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
    priority: Annotated[int | None, Query(ge=1, le=5)] = None,
) -> Sequence[Task]:
    now = datetime.now(UTC)
    today_end = datetime.combine(now.date(), time.max, tzinfo=UTC)
    today_start = datetime.combine(now.date(), time.min, tzinfo=UTC)
    query = (
        select(Task)
        .where(Task.owner_id == current_user.id)
        .where(col(Task.due_date).between(today_start, today_end))
        .where(col(Task.completed).is_(False))
    )
    if priority is not None:
        query = query.where(Task.priority == priority)
    results = await session.exec(query.offset(offset).limit(limit))
    return results.all()


@router.get("/overdue", response_model=list[TaskPublic])
async def read_overdue_tasks(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
    priority: Annotated[int | None, Query(ge=1, le=5)] = None,
) -> Sequence[Task]:
    now = datetime.now(UTC)
    query = (
        select(Task)
        .where(Task.owner_id == current_user.id)
        .where(col(Task.due_date) < now)
        .where(col(Task.completed).is_(False))
    )
    if priority is not None:
        query = query.where(Task.priority == priority)
    results = await session.exec(query.offset(offset).limit(limit))
    return results.all()


@router.get("/{task_id}", response_model=TaskPublicWithProject)
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return task


@router.put("/{task_id}/projects/{project_id}", response_model=TaskPublicWithProject)
async def assign_task_to_project(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    task_id: Annotated[uuid.UUID, Path()],
    project_id: Annotated[uuid.UUID, Path()],
) -> Task:
    results = await session.exec(
        select(Task).where(Task.id == task_id, Task.owner_id == current_user.id)
    )
    task = results.first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    results = await session.exec(
        select(Project).where(
            Project.id == project_id, Project.owner_id == current_user.id
        )
    )
    project = results.first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    task.project_id = project.id
    await session.commit()
    await session.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskPublicWithProject)
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    await session.delete(task)
    await session.commit()


@router.delete("/{task_id}/projects/{project_id}", response_model=TaskPublicWithProject)
async def remove_task_from_project(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    task_id: Annotated[uuid.UUID, Path()],
    project_id: Annotated[uuid.UUID, Path()],
) -> Task:
    results = await session.exec(
        select(Task).where(Task.id == task_id, Task.owner_id == current_user.id)
    )
    task = results.first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    results = await session.exec(
        select(Project).where(
            Project.id == project_id, Project.owner_id == current_user.id
        )
    )
    project = results.first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    task.project_id = None
    await session.commit()
    await session.refresh(task)
    return task
