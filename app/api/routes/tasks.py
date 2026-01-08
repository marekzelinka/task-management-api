from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Query, status
from sqlmodel import select

from app.api.deps import SessionDep
from app.models import Task, TaskCreate, TaskPublic, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskPublic, status_code=status.HTTP_201_CREATED)
def create_task(*, session: SessionDep, task: Annotated[TaskCreate, Body()]):
    db_task = Task.model_validate(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


@router.get("/", response_model=list[TaskPublic])
def read_tasks(
    *,
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
    completed: Annotated[bool | None, Query()] = None,
):
    query = select(Task)
    if completed is not None:
        query = query.where(Task.completed == completed)
    tasks = session.exec(query.offset(offset).limit(limit)).all()
    return tasks


@router.get("/{task_id}", response_model=TaskPublic)
def read_task(*, session: SessionDep, task_id: Annotated[str, Path()]):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    return task


@router.patch("/{task_id}", response_model=TaskPublic)
def update_task(
    *,
    session: SessionDep,
    task_id: Annotated[str, Path()],
    task: Annotated[TaskUpdate, Body()],
):
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    task_data = task.model_dump(exclude_unset=True)
    db_task.sqlmodel_update(task_data)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(*, session: SessionDep, task_id: Annotated[str, Path()]):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    session.delete(task)
    session.commit()
