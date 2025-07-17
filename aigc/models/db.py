from sqlmodel import SQLModel, Field
from enum import StrEnum, IntEnum
from datetime import datetime
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy import Column

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
    edit_with_prompt = 5

    def __str__(self) -> str:
        names = {
            InferenceType.replace_with_any: "replace any",
            InferenceType.replace_with_reference: "replace with reference",
            InferenceType.segment_any: "segment any",
            InferenceType.image_to_video: "image to video",
            InferenceType.edit_with_prompt: "edit with prompt"
        }
        return names[self]


class InferenceState(IntEnum):
    waiting = 0
    in_progress = 1
    down = 2
    failed = 3
    canceled = 4

    def __str__(self) -> str:
        names = {
            InferenceState.waiting: "waiting",
            InferenceState.in_progress: "in progress",
            InferenceState.down: "down",
            InferenceState.failed: "failed",
            InferenceState.canceled: "canceled",
        }
        return names[self]


class InferenceLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    uid: int = Field(index=True)
    tid: str = Field(index=True)
    type: InferenceType
    point: int
    state: InferenceState = InferenceState.waiting
    ctime: datetime = Field(default_factory=datetime.now)
    utime: datetime = Field(default_factory=datetime.now)
    request: str =  Field(default="", sa_column=Column(LONGTEXT))
    response: str = Field(default="", sa_column=Column(LONGTEXT))
