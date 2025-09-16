from .category import Category
from typing import Sequence
from models.logs import Log, LogLevel


class OpLogger:

    async def info(
        self, category: Category, title: str, detail: str | Sequence[str] | None = None
    ) -> None:
        log = Log(level=LogLevel.info, category=category, title=title, detail=detail)
        await log.save()

    async def warning(
        self, category: Category, title: str, detail: str | Sequence[str] | None = None
    ) -> None:
        log = Log(level=LogLevel.warning, category=category, title=title, detail=detail)
        await log.save()

    async def error(
        self, category: Category, title: str, detail: str | Sequence[str] | None = None
    ) -> None:
        log = Log(level=LogLevel.error, category=category, title=title, detail=detail)
        await log.save()
