from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import CurrentUserDep, PaginationParamsDep, SessionDep
from app.models import (
    Paged,
    ProjectCreate,
    ProjectPublic,
    ProjectUpdate,
    TaskPublic,
)
from app.schema import Project, Task

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProjectPublic)
async def create_project(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    project: ProjectCreate,
) -> Project:
    db_project = Project(**project.model_dump(), owner_id=current_user.id)

    session.add(db_project)

    await session.commit()
    await session.refresh(db_project)

    return db_project


@router.get("", response_model=Paged[ProjectPublic])
async def read_projects(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    paging: PaginationParamsDep,
) -> Paged[Project]:
    query = select(Project).where(Project.owner_id == current_user.id)

    total = await session.execute(select(func.count()).select_from(query.subquery()))
    projects = await session.scalars(query.offset(paging.offset).limit(paging.limit))

    return Paged(
        page=paging.page,
        per_page=paging.per_page,
        total=total.scalar_one(),
        results=projects.all(),
    )


@router.get("/{project_id}", response_model=ProjectPublic)
async def read_project(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    project_id: int,
) -> Project:
    project = await session.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.get("/{project_id}/tasks", response_model=Paged[TaskPublic])
async def read_project_tasks(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    project_id: int,
    paging: PaginationParamsDep,
) -> Paged[Task]:
    project = await session.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    query = select(Task).where(Task.project_id == project_id)

    total = await session.execute(select(func.count()).select_from(query.subquery()))
    tasks = await session.scalars(query.offset(paging.offset).limit(paging.limit))

    return Paged(
        page=paging.page,
        per_page=paging.per_page,
        total=total.scalar_one(),
        results=tasks.all(),
    )


@router.patch("/{project_id}", response_model=ProjectPublic)
async def update_project(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    project_id: int,
    project: ProjectUpdate,
) -> Project:
    db_project = await session.get(Project, project_id)
    if not db_project or db_project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    update_data = project.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)

    await session.commit()
    await session.refresh(db_project)

    return db_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    project_id: int,
) -> None:
    project = await session.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    await session.delete(project)
    await session.commit()
