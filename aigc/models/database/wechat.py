from sqlmodel import SQLModel, Field


class UserInfo(SQLModel, table=True):

    __tablename__ = "wechat_user_info"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    openid: str = Field(index=True)
    uid: int = Field(index=True)
    avatar: str
    nickname: str
    unionid: str = Field(index=True)
