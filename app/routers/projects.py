import uuid
from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Query, status
from sqlmodel import select

from app.deps import CurrentUserDep, SessionDep
from app.models import (
    Project,
    ProjectCreate,
    ProjectPublic,
    ProjectPublicWithTasks,
    ProjectUpdate,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProjectPublic)
async def create_project(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    project: Annotated[ProjectCreate, Body()],
) -> Project:
    db_project = Project.model_validate(project, update={"owner_id": current_user.id})
    session.add(db_project)
    await session.commit()
    await session.refresh(db_project)
    return db_project


@router.get("/", response_model=list[ProjectPublic])
async def read_projects(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(gt=0)] = 100,
) -> Sequence[Project]:
    results = await session.exec(
        select(Project)
        .where(Project.owner_id == current_user.id)
        .offset(offset)
        .limit(limit)
    )
    return results.all()


@router.get("/{project_id}", response_model=ProjectPublicWithTasks)
async def read_project(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    project_id: Annotated[uuid.UUID, Path()],
) -> Project:
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
    return project


@router.patch("/{project_id}", response_model=ProjectPublic)
async def update_project(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    project_id: Annotated[uuid.UUID, Path()],
    project: Annotated[ProjectUpdate, Body()],
) -> Project:
    results = await session.exec(
        select(Project).where(
            Project.id == project_id, Project.owner_id == current_user.id
        )
    )
    db_project = results.first()
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    project_data = project.model_dump(exclude_unset=True)
    db_project.sqlmodel_update(project_data)
    session.add(db_project)
    await session.commit()
    await session.refresh(db_project)
    return db_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    project_id: Annotated[uuid.UUID, Path()],
) -> None:
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
    await session.delete(project)
    await session.commit()
