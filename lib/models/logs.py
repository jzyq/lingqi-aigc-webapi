from beanie import Document
from enum import StrEnum
from datetime import datetime
from pydantic import Field
from typing import Sequence
from pymongo.asynchronous.database import AsyncDatabase


async def init(db: AsyncDatabase) -> None:
    from beanie import init_beanie

    await init_beanie(db, document_models=[Log])


class LogLevel(StrEnum):
    info = "info"
    warning = "warning"
    error = "error"


class Log(Document):
    level: LogLevel
    ctime: datetime = Field(default_factory=datetime.now)
    category: str
    title: str
    detail: str | Sequence[str] | None = None

    class Settings:
        name = "oplogs"
