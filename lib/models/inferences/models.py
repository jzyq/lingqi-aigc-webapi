from pydantic import BaseModel
from enum import StrEnum
from typing import Any


class DataSource(StrEnum):
    in_place = "in_place"
    gridfs = "gridfs"


class Request(BaseModel):
    url: str
    data_source: DataSource
    data: dict[str, Any]
    ipt_sys_prompt: str | None = None
    ipt_user_prompt: str | None = None
    aigc_prompt: str | None = None

    @staticmethod
    def in_place(
        url: str,
        data: dict[str, Any],
        ipt_sys_prompt: str | None = None,
        ipt_user_prompt: str | None = None,
        aigc_prompt: str | None = None,
    ) -> "Request":
        return Request(
            url=url,
            data_source=DataSource.in_place,
            data=data,
            ipt_sys_prompt=ipt_sys_prompt,
            ipt_user_prompt=ipt_user_prompt,
            aigc_prompt=aigc_prompt,
        )


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
