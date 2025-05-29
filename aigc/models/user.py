
from datetime import datetime
from pydantic import BaseModel


class GetUserInfoResponse(BaseModel):
    username: str
    nickname: str
    avatar: str
    point: int
    expires_in: datetime | None
