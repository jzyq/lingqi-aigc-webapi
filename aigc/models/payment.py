from pydantic import BaseModel
from sqlmodel import SQLModel, Field
from datetime import datetime
from enum import StrEnum


class PayState(StrEnum):
    on_going = "on going"
    success = "success"
    failed = "failed"
    refund = "refund"


class OpenPaymentRequest(BaseModel):
    amount: int


class OpenPaymentResponse(BaseModel):
    url: str
    tradeid: str


class PayCallbackResource(BaseModel):
    original_type: str
    algorithm: str
    ciphertext: str
    associated_data: str
    nonce: str


class PayCallbackRequest(BaseModel):
    id: str
    create_time: str
    resource_type: str
    event_type: str
    summary: str
    resource: PayCallbackResource


class PayCallbackAmount(BaseModel):
    total: int
    payer_total: int
    currency: str
    payer_currency: str


class PayCallbackPayerInfo(BaseModel):
    openid: str


class PayCallbackResult(BaseModel):
    mchid: str
    appid: str
    out_trade_no: str
    transaction_id: str
    trade_type: str
    trade_state: str
    trade_state_desc: str
    bank_type: str
    attach: str
    success_time: str
    amount: PayCallbackAmount
    payer: PayCallbackPayerInfo


class GetPaymentStateResponse(BaseModel):
    tradeid: str
    state: PayState
    desc: str | None = None


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
