from fastapi import APIRouter
from . import deps, wx, models, config, common
from loguru import logger
from datetime import datetime, timedelta

router = APIRouter(prefix="/payment")


@router.post("/open")
async def open_payment(req: models.payment.OpenPaymentRequest,
                       ses: deps.UserSession, wx_client: deps.WxClient,
                       db: deps.Database) -> models.payment.OpenPaymentResponse:

    conf = config.Config()
    dt = datetime.now()
    tradeid = wx.make_nonce_str(16)
    desc = f"充值"
    expires_in = dt + timedelta(seconds=conf.payment_expires_in_s)

    logger.info(
        f"user open new recharge order {tradeid}, amount {req.amount / 100} CNY")

    order = wx.models.Order(description=desc, out_trade_no=tradeid,
                            notify_url=conf.wx_payment_callback,
                            amount=wx.models.PayAmount(total=req.amount),
                            time_expire=common.format_datetime(expires_in))

    url = await wx_client.open_transaction(order)
    logger.info(f"recharge order {tradeid} pay url: {url}")

    payment = models.payment.Recharge(
        uid=ses.uid, tradeid=tradeid, amount=req.amount, create_time=dt, expires=expires_in)
    db.add(payment)
    db.commit()

    return models.payment.OpenPaymentResponse(url=url, tradeid=tradeid)
