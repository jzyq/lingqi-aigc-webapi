from enum import IntEnum
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import TEXT, LONGTEXT
from datetime import datetime


class Type(IntEnum):
    replace_with_any = 1
    replace_with_reference = 2
    segment_any = 3
    image_to_video = 4
    edit_with_prompt = 5

    def __str__(self) -> str:
        names = {
            Type.replace_with_any: "replace any",
            Type.replace_with_reference: "replace with reference",
            Type.segment_any: "segment any",
            Type.image_to_video: "image to video",
            Type.edit_with_prompt: "edit with prompt",
        }
        return names[self]


class State(IntEnum):
    waiting = 0
    in_progress = 1
    down = 2
    failed = 3
    canceled = 4

    def __str__(self) -> str:
        names = {
            State.waiting: "waiting",
            State.in_progress: "in progress",
            State.down: "down",
            State.failed: "failed",
            State.canceled: "canceled",
        }
        return names[self]


class Log(SQLModel, table=True):

    __tablename__ = "inference_log"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    uid: int = Field(index=True)
    tid: str = Field(index=True)
    type: Type
    point: int
    url: str = Field(sa_column=Column(TEXT))
    state: State = State.waiting
    ctime: datetime = Field(default_factory=datetime.now)
    utime: datetime = Field(default_factory=datetime.now)
    request: str = Field(default="", sa_column=Column(LONGTEXT))
    response: str = Field(default="", sa_column=Column(LONGTEXT))
