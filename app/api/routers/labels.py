from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import CurrentUserDep, PaginationParamsDep, SessionDep
from app.models import LabelCreate, LabelPublic, LabelUpdate, Paged, TaskPublic
from app.schema import Label, Task

router = APIRouter(prefix="/labels", tags=["labels"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LabelPublic)
async def create_label(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    label: LabelCreate,
) -> Label:
    existing_label = await session.scalar(select(Label).where(Label.name == label.name))
    if existing_label:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Label already exists"
        )

    db_label = Label(**label.model_dump(), owner_id=current_user.id)

    session.add(db_label)

    await session.commit()
    await session.refresh(db_label)

    return db_label


@router.get("", response_model=Paged[LabelPublic])
async def read_labels(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    paging: PaginationParamsDep,
    # TODO: add filter query `q`, to fetch labels where name contains `q`
) -> Paged[Label]:
    query = select(Label).where(Label.owner_id == current_user.id)

    total = await session.execute(select(func.count()).select_from(query.subquery()))
    labels = await session.scalars(query.offset(paging.offset).limit(paging.limit))

    return Paged(
        page=paging.page,
        per_page=paging.per_page,
        total=total.scalar_one(),
        results=labels.all(),
    )


@router.get("/{label_id}/tasks", response_model=Paged[TaskPublic])
async def read_label_tasks(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    label_id: int,
    paging: PaginationParamsDep,
) -> Paged[Task]:
    label = await session.get(Label, label_id)
    if not label or label.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    query = select(Task).where(Task.labels.any(Label.id == label_id))

    total = await session.execute(select(func.count()).select_from(query.subquery()))
    tasks = await session.scalars(query.offset(paging.offset).limit(paging.limit))

    return Paged(
        page=paging.page,
        per_page=paging.per_page,
        total=total.scalar_one(),
        results=tasks.all(),
    )


@router.patch("/{label_id}", response_model=LabelPublic)
async def update_label(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    label_id: int,
    label: LabelUpdate,
) -> Label:
    db_label = await session.get(Label, label_id)
    if not db_label or db_label.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Label not found"
        )

    update_data = label.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_label, field, value)

    await session.commit()
    await session.refresh(db_label)

    return db_label


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    label_id: int,
) -> None:
    label = await session.get(Label, label_id)
    if not label or label.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Label not found"
        )

    await session.delete(label)
    await session.commit()
