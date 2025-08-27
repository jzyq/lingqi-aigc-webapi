from pydantic import BaseModel
from enum import StrEnum


class UserSource(StrEnum):
    local = "local"
    wx_openid = "openid"


class UserID(BaseModel):
    source: UserSource
    ident: str
