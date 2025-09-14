from enum import StrEnum
from datetime import datetime

from pydantic import Field
from .. import users
from beanie import Document

from .models import *

from typing import Sequence


class Gender(StrEnum):
    male = "男"
    female = "女"
    other = "其他"


class State(StrEnum):
    prepare = "prepare"
    waiting = "waiting"
    processing = "processing"
    down = "down"
    error = "error"
    cancel = "canceled"


class Inference(Document):
    uid: users.UserID
    userdata: str
    callback: str
    state: State = State.prepare
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


class HeavenAlbum(Inference):
    inference_endpoint: str
    
    nickname: str
    picture: str
    gender: Gender
    faith: Sequence[str]
    hobby: Sequence[str]

    ipt_sys_prompt: str | None = None
    ipt_user_prompt: str | None = None
    model: str | None = None
    aigc_prompts: Sequence[str] = []
    norimalized_picture: str | None = None
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

    async def set_ready(self) -> None:
        self.utime = datetime.now()
        self.state = State.waiting
        await self.save()


class CallbackData(BaseModel):
    userdata: str
    state: State
    result: StandardResponse | CompositeResponse | None = None
