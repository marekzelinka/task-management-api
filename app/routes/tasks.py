from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database.config import get_session
from app.models.task import Task, TaskCreate, TaskRead

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(*, session: Session = Depends(get_session), task: TaskCreate):
    db_task = Task.from_orm(task)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


@router.get("/", response_model=list[TaskRead])
def read_tasks(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = 100,
    completed: bool | None = None,
):
    query = select(Task)

    if completed is not None:
        query = query.where(Task.completed == completed)

    tasks = session.exec(query.offset(offset).limit(limit)).all()
    return tasks


@router.get("/{task_id}", response_model=TaskRead)
def read_task(*, session: Session = Depends(get_session), task_id: str):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    return task


@router.put("/{task_id}", response_model=TaskRead)
def update_task(
    *, session: Session = Depends(get_session), task_id: str, task: TaskCreate
):
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )

    task_data = task.dict()
    for key, value in task_data.items():
        setattr(db_task, key, value)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(*, session: Session = Depends(get_session), task_id: str):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    session.delete(task)
    session.commit()
    return None
