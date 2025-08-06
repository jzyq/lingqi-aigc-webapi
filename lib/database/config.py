from sqlmodel import SQLModel, Field
from enum import StrEnum
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import LONGTEXT


class SystemConfigCategory(StrEnum):
    wechat = "wechat"
    session = "session"


class SystemConfig(SQLModel, table=True):

    __tablename__ = "system_config"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    category: SystemConfigCategory
    name: str
    value: str = Field(sa_column=Column(LONGTEXT))
