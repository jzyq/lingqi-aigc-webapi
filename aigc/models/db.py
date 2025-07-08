from sqlmodel import SQLModel, Field
from enum import StrEnum, IntEnum
from datetime import datetime


class SubscriptionType(StrEnum):
    trail = "trail"
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
    ctime: datetime = Field(default_factory=datetime.now)
    utime: datetime = Field(default_factory=datetime.now)
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


class SubscriptionsRefreshLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    refresh_time: datetime
    cnt: int


class InferenceType(IntEnum):
    replace_with_any = 1
    replace_with_reference = 2
    segment_any = 3
    image_to_video = 4


class InferenceState(IntEnum):
    waiting = 0
    in_progress = 1
    down = 2
    canceled = 3


class InferenceLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uid: int
    type: InferenceType
    state: InferenceState
    ctime: datetime = Field(default_factory=datetime.now)
    utime: datetime = Field(default_factory=datetime.now)
    request: str = ""
    response: str = ""
