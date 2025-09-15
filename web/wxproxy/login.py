from fastapi import APIRouter
from pydantic import BaseModel
from dataio import config


router = APIRouter(prefix="/login")


class GetQRCodeLoginUrlResponse(BaseModel):
    url: str


@router.get("/qrcode")
async def gen_qrcode_login_url(
    state: str
) -> GetQRCodeLoginUrlResponse:
    conf = await config.wechat.Login.get()

    url = (
        "https://open.weixin.qq.com/connect/qrconnect"
        + f"?appid={conf.appid}"
        + f"&redirect_uri={conf.redirect_url}"
        + "&response_type=code&scope=snsapi_login"
        + f"&state={state}"
        + "#wechat_redirect"
    )

    return GetQRCodeLoginUrlResponse(url=url)
