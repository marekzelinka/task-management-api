from sqlmodel import SQLModel, create_engine

from app.core.config import config

engine = create_engine(str(config.database_url))


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
