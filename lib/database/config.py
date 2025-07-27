from sqlmodel import SQLModel, Field
from enum import StrEnum
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import LONGTEXT
from datetime import datetime


class Category(StrEnum):
    wechat = "wechat"


class Config(SQLModel, table=True):

    __tablename__ = "config"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    category: Category
    name: str
    revision: int
    ctime: datetime = Field(default_factory=datetime.now)
    value: str = Field(sa_column=Column(LONGTEXT))
