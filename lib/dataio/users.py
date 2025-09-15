from pydantic import BaseModel
from datetime import datetime


class UserInfo(BaseModel):
    id: str
    username: str
    nickname: str
    avatar: str
    phone: str | None = None
    wx_openid: str | None = None

    @staticmethod
    async def get(uid: str) -> "UserInfo":
        raise NotImplementedError()

    async def save(self) -> str:
        raise NotImplementedError()

    async def is_member(self) -> bool:
        raise NotImplementedError()

    async def remain_point(self) -> int:
        raise NotImplementedError()
    
    async def member_expires(self) -> datetime | None:
        raise NotImplementedError()
