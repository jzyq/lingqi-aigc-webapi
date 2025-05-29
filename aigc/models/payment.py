from pydantic import BaseModel
from . import db


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
    state: db.PayState
    desc: str | None = None
