from sqlmodel import SQLModel, Field
from enum import StrEnum
from datetime import datetime


class Type(StrEnum):
    trail = "trail"
    subscription = "subscription"


class ExpiresUnit(StrEnum):
    day = "day"
    month = "month"


class RefreshLog(SQLModel, table=True):

    __tablename__ = "subscription_refresh_log"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    refresh_time: datetime
    cnt: int


class Subscription(SQLModel, table=True):

    __tablename__ = "subscriptions"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    uid: int
    stype: Type
    init: int
    remains: int
    ctime: datetime = Field(default_factory=datetime.now)
    utime: datetime = Field(default_factory=datetime.now)
    expires_in: datetime | None = None
    expired: bool = False


class SubscriptionPlans(SQLModel, table=True):

    __tablename__ = "subscription_plans"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    stype: Type
    point: int
    expires: int
    unit: ExpiresUnit
    price: int
    enable: bool = False
