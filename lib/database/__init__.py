from . import config, inference, subscription, user, pay, wechat  # type: ignore
from sqlalchemy import Engine
from sqlmodel import create_engine  # type: ignore


def create_all_tables(engine: Engine) -> None:
    from sqlmodel import SQLModel

    SQLModel.metadata.create_all(engine)
