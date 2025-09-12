from pydantic import BaseModel
from enum import StrEnum
from typing import Any


class DataSource(StrEnum):
    in_place = "in_place"
    gridfs = "gridfs"


class Request(BaseModel):
    url: str
    image_source: DataSource
    image: str
    ipt_sys_prompt: str | None = None
    ipt_user_prompt: str | None = None
    aigc_prompt: str | None = None
    model: str | None = None


class StandardResponse(BaseModel):
    code: int = 0
    msg: str = "ok"
    data: str = ""


class CompositeResponse(BaseModel):
    code: int = 0
    msg: str = "ok"
    data: list[str] = []


class InferenceResult(BaseModel):
    code: int
    msg: str
    cost_time: str | None = None
    data: list[str] | None = None
