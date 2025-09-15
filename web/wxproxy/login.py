from fastapi import APIRouter
from pydantic import BaseModel
from dataio import config


router = APIRouter(prefix="/login")


class GetQRCodeLoginUrlRequest(BaseModel):
    redirect_url: str
    state: str


class GetQRCodeLoginUrlResponse(BaseModel):
    url: str


@router.get("/qrcode")
async def gen_qrcode_login_url(
    req: GetQRCodeLoginUrlRequest,
) -> GetQRCodeLoginUrlResponse:
    conf = await config.wechat.Login.get()

    url = (
        "https://open.weixin.qq.com/connect/qrconnect"
        + f"?appid={conf.appid}"
        + f"&redirect_uri={req.redirect_url}"
        + "&response_type=code&scope=snsapi_login"
        + f"&state={req.state}"
        + "#wechat_redirect"
    )

    return GetQRCodeLoginUrlResponse(url=url)
