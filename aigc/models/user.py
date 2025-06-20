
from datetime import datetime
from pydantic import BaseModel


class GetUserInfoResponse(BaseModel):
    username: str
    nickname: str
    avatar: str
    point: int
    is_member: bool
    expires_in: datetime | None
