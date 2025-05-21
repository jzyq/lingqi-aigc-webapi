from sqlmodel import SQLModel, Field


class WxUserInfo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    open_id: str
    avatar: str
    nickname: str
    unionid: str = Field(index=True)
