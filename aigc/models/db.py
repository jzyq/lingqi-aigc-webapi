from sqlmodel import SQLModel, Field
from enum import StrEnum
from datetime import datetime


class SubscriptionType(StrEnum):
    subscription = "subscription"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=128)
    nickname: str = Field(max_length=128)
    avatar: str
    phone: str | None = None
    wx_id: str | None = Field(default=None, index=True)


class MagicPointSubscription(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uid: int
    stype: SubscriptionType
    init: int
    remains: int
    ctime: datetime
    utime: datetime
    expires_in: datetime | None = None
    expired: bool = False


class WxUserInfo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    openid: str = Field(index=True)
    uid: int = Field(index=True)
    avatar: str
    nickname: str
    unionid: str = Field(index=True)


class PayState(StrEnum):
    on_going = "on going"
    success = "success"
    failed = "failed"
    refund = "refund"


class Recharge(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uid: int = Field(index=True)
    tradeid: str = Field(index=True)
    amount: int
    create_time: datetime
    expires: datetime
    transaction_id: str | None = None
    success_time: datetime | None = None
    reason: str | None = None
    pay_state: PayState = PayState.on_going
