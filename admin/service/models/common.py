from pydantic import BaseModel
from typing import Any


class APIResponse(BaseModel):
    code: int = 0
    msg: str = "ok"
    data: Any | None = None
