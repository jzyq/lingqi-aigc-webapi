import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dataio.config import wechat
from dataio import errors
from loguru import logger
import oplog


class LoginQRCode(BaseModel):
    url: str


router = APIRouter(prefix="/login")


@router.get("/qrcode")
async def generate_qrcode_login_url(state: str) -> LoginQRCode:
    try:
        conf = await wechat.Login.get()
    except errors.NotExists as exc:
        logger.error(f"try get wechat login config but not exists")
        await oplog.logger.error(
            oplog.Category.webapi, "no wechat login config", traceback.format_exc()
        )
        raise HTTPException(500, detail="no wechat login config") from exc

    url = (
        "https://open.weixin.qq.com/connect/qrconnect"
        + f"?appid={conf.appid}"
        + f"&redirect_uri={conf.redirect_url}"
        + "&response_type=code&scope=snsapi_login"
        + f"&state={state}"
        + "#wechat_redirect"
    )

    return LoginQRCode(url=url)
