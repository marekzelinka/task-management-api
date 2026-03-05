from datetime import UTC, datetime, time
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from app.api.deps import CurrentUserDep, PaginationParamsDep, SessionDep
from app.models import (
    Paged,
    TaskCreate,
    TaskPublic,
    TaskPublicWithLabels,
    TaskPublicWithProject,
    TaskPublicWithProjectLabels,
    TaskUpdate,
)
from app.schema import Label, Project, Task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TaskPublic)
async def create_task(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    task: TaskCreate,
) -> Task:
    if task.project_id is not None:
        project = await session.get(Project, task.project_id)
        if not project or project.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project not found",
            )

    db_task = Task(**task.model_dump(), owner_id=current_user.id)

    session.add(db_task)

    await session.commit()
    await session.refresh(db_task)

    return db_task


@router.post(
    "/{task_id}/duplicate",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskPublicWithProjectLabels,
)
async def create_duplicate_task(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    task_id: int,
) -> Task:
    task = await session.get(
        Task, task_id, options=[joinedload(Task.project), selectinload(Task.labels)]
    )
    if not task or task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Task not found"
        )
    if task.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Task is completed"
        )

    db_task = Task(
        title=f"{task.title} (Copy)",
        description=task.description,
        priority=task.priority,
        completed=task.completed,
        due_date=task.due_date,
        owner_id=task.owner_id,
        project_id=task.project_id,
    )
    db_task.labels = list(task.labels)

    session.add(db_task)

    await session.commit()
    await session.refresh(db_task, attribute_names={"project", "labels"})

    return db_task


@router.get("", response_model=Paged[TaskPublic])
async def read_tasks(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    paging: PaginationParamsDep,
    completed: Annotated[bool | None, Query()] = None,
    priority: Annotated[int | None, Query(ge=1, le=5)] = None,
) -> Paged[Task]:
    query = select(Task).where(Task.owner_id == current_user.id)
    if completed is not None:
        query = query.where(Task.completed == completed)
    if priority is not None:
        query = query.where(Task.priority == priority)

    total = await session.execute(select(func.count()).select_from(query.subquery()))
    tasks = await session.scalars(query.offset(paging.offset).limit(paging.limit))

    return Paged(
        page=paging.page,
        per_page=paging.per_page,
        total=total.scalar_one(),
        results=tasks.all(),
    )


@router.get("/upcomming", response_model=Paged[TaskPublic])
async def read_upcomming_tasks(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    paging: PaginationParamsDep,
    priority: Annotated[int | None, Query(ge=1, le=5)] = None,
) -> Paged[Task]:
    now = datetime.now(tz=UTC)

    query = (
        select(Task)
        .where(Task.owner_id == current_user.id)
        .where(Task.due_date > now)
        .where(~Task.completed)
    )
    if priority is not None:
        query = query.where(Task.priority == priority)

    total = await session.execute(select(func.count()).select_from(query.subquery()))
    tasks = await session.scalars(
        query.order_by(Task.due_date.asc().nulls_last())
        .offset(paging.offset)
        .limit(paging.limit)
    )

    return Paged(
        page=paging.page,
        per_page=paging.per_page,
        total=total.scalar_one(),
        results=tasks.all(),
    )


@router.get("/today", response_model=Paged[TaskPublic])
async def read_due_today_tasks(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    paging: PaginationParamsDep,
    priority: Annotated[int | None, Query(ge=1, le=5)] = None,
) -> Paged[Task]:
    now = datetime.now(tz=UTC)
    today_end = datetime.combine(now.date(), time.max, tzinfo=UTC)
    today_start = datetime.combine(now.date(), time.min, tzinfo=UTC)

    query = (
        select(Task)
        .where(Task.owner_id == current_user.id)
        .where(Task.due_date.between(today_start, today_end))
        .where(~Task.completed)
    )
    if priority is not None:
        query = query.where(Task.priority == priority)

    total = await session.execute(select(func.count()).select_from(query.subquery()))
    tasks = await session.scalars(query.offset(paging.offset).limit(paging.limit))

    return Paged(
        page=paging.page,
        per_page=paging.per_page,
        total=total.scalar_one(),
        results=tasks.all(),
    )


@router.get("/overdue", response_model=Paged[TaskPublic])
async def read_overdue_tasks(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    paging: PaginationParamsDep,
    priority: Annotated[int | None, Query(ge=1, le=5)] = None,
) -> Paged[Task]:
    now = datetime.now(tz=UTC)

    query = (
        select(Task)
        .where(Task.owner_id == current_user.id)
        .where(Task.due_date < now)
        .where(~Task.completed)
    )
    if priority is not None:
        query = query.where(Task.priority == priority)

    total = await session.execute(select(func.count()).select_from(query.subquery()))
    tasks = await session.scalars(query.offset(paging.offset).limit(paging.limit))

    return Paged(
        page=paging.page,
        per_page=paging.per_page,
        total=total.scalar_one(),
        results=tasks.all(),
    )


@router.get("/{task_id}", response_model=TaskPublicWithProjectLabels)
async def read_task(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    task_id: int,
) -> Task:
    task = await session.get(
        Task, task_id, options=[joinedload(Task.project), selectinload(Task.labels)]
    )
    if not task or task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    return task


@router.patch("/{task_id}", response_model=TaskPublicWithProject)
async def update_task(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    task_id: int,
    task: TaskUpdate,
) -> Task:
    db_task = await session.get(Task, task_id)
    if not db_task or db_task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    if task.project_id is not None:
        project = await session.get(Project, task.project_id)
        if not project or project.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project not found",
            )

    update_data = task.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    await session.commit()
    await session.refresh(db_task, attribute_names={"project"})

    return db_task


@router.post("/{task_id}/labels/{label_id}", response_model=TaskPublicWithLabels)
async def assign_label_to_task(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    task_id: int,
    label_id: int,
) -> Task:
    task = await session.get(Task, task_id, options=[selectinload(Task.labels)])
    if not task or task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    label = await session.get(Label, label_id)
    if not label or label.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Label not found"
        )
    if label in task.labels:
        raise HTTPException(
            status_code=status.HTTP_304_NOT_MODIFIED,
            detail="Label already assigned to task",
        )

    task.labels.append(label)

    await session.commit()
    await session.refresh(task, attribute_names={"labels"})

    return task


@router.delete("/{task_id}/labels/{label_id}", response_model=TaskPublicWithLabels)
async def remove_label_from_task(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    task_id: int,
    label_id: int,
) -> Task:
    task = await session.get(Task, task_id, options=[selectinload(Task.labels)])
    if not task or task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    label = next((label for label in task.labels if label.id == label_id), None)
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Label not assigned to task"
        )

    task.labels.remove(label)

    await session.commit()
    await session.refresh(task, attribute_names={"labels"})

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    task_id: int,
) -> None:
    task = await session.get(Task, task_id)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    await session.delete(task)
    await session.commit()
