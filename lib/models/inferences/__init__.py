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
    error = "error"
    cancel = "canceled"


class Inference(Document):
    uid: users.UserID
    userdata: str
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
    response: StandardResponse | None = None

    async def set_success(self, url: str) -> None:
        self.response = StandardResponse(data=url)
        self.utime = datetime.now()
        self.state = State.down
        await self.save()

    async def set_error(self, code: int, msg: str) -> None:
        self.response = StandardResponse(code=code, msg=msg)
        self.utime = datetime.now()
        self.state = State.error
        await self.save()


class CompositeTask(Inference):
    requests: list[Request]
    response: CompositeResponse | None = None

    async def add_data(self, data: str) -> None:
        if not self.response:
            self.response = CompositeResponse()
        self.response.data.append(data)
        self.utime = datetime.now()
        await self.save()

    async def set_success(self) -> None:
        self.utime = datetime.now()
        self.state = State.down
        await self.save()

    async def set_error(self, code: int, msg: str) -> None:
        self.response = CompositeResponse(code=code, msg=msg)
        self.utime = datetime.now()
        self.state = State.error
        await self.save()


class CallbackData(BaseModel):
    userdata: str
    state: State
    result: StandardResponse | CompositeResponse | None = None
