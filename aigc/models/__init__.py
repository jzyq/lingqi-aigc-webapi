from sqlmodel import create_engine, SQLModel, Session
from typing import Annotated
from sqlalchemy import Engine
from fastapi import Depends

engine: Engine


def get_session():
    with Session(engine) as session:
        yield session


DBSessionDep = Annotated[Session, Depends(get_session)]


def initialize_database_io(db_file_name: str):
    sqlite_url = f"sqlite:///{db_file_name}"
    connect_args = {"check_same_thread": False}

    global engine
    engine = create_engine(sqlite_url, connect_args=connect_args)

    SQLModel.metadata.create_all(engine)
