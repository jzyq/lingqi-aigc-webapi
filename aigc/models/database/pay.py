from sqlmodel import SQLModel, Field
from enum import StrEnum
from datetime import datetime


class State(StrEnum):
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
    pay_state: State = State.on_going
