from beanie import Document
from enum import StrEnum
from datetime import datetime
from pydantic import Field
from typing import Sequence


class LogLevel(StrEnum):
    info = "info"
    error = "error"


class Logs(Document):
    level: LogLevel
    ctime: datetime = Field(default_factory=datetime.now)
    category: str
    title: str
    detail: str | Sequence[str] | None = None

    class Settings:
        name = "oplogs"