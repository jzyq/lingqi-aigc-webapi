from enum import StrEnum
from datetime import datetime

from pydantic import Field
from .. import users
from beanie import Document

from .models import *


class State(StrEnum):
    waiting = "waiting"
    processing = "processing"
    down = "down"
    cancel = "canceled"


class Inference(Document):
    uid: users.UserID
    tid: str
    callback: str
    state: State = State.waiting
    ctime: datetime = Field(default_factory=datetime.now)
    utime: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "inferences"
        is_root = True
        class_id = "type"


class StandardTask(Inference):
    request: Request
    response: Response | None = None


class CompositeTask(Inference):
    requests: list[Request]
    response: list[Response] = []
