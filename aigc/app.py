from fastapi import FastAPI, Request, HTTPException, Header, Response
from fastapi.responses import RedirectResponse
import requests
from pydantic import BaseModel
from typing import Optional, Union, Annotated
import random
from . import deps
from .models import user
from .wx import client
import json


random.seed()
app = FastAPI()

TOKEN_LEN = 16

HeaderField = Annotated[str, Header()]


class AuthCode(BaseModel):
    code: str
    state: Optional[str] = None


user_infos: dict[str, user.WxUserInfo] = {}


def generate_random_hex_str(length: int) -> str:
    seq = random.choices("1234567890abcdef", k=length)
    return "".join(seq)


@app.get("/api/wx/login/callback")
async def wechat_login_callback(request: Request, db: deps.DBSession, wx: deps.WxClient):
    """
    微信扫码登录回调接口
    流程：1. 接收code -> 2. 换取access_token -> 3. 获取用户信息
    """
    # Step 1: 获取授权码和state参数
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code:
        raise HTTPException(
            status_code=400, detail="Missing authorization code")

    # Step 2: 用code换取access_token
    app_id = wx.sec.app_id
    app_secret = wx.sec.app_secret
    token_url = f"https://api.weixin.qq.com/sns/oauth2/access_token?appid={app_id}&secret={app_secret}&code={code}&grant_type=authorization_code"

    try:
        token_res = requests.get(token_url)
        token_data = token_res.json()

        if "errcode" in token_data:
            raise HTTPException(
                status_code=400, detail=f"WeChat API error: {token_data.get('errmsg')}"
            )

        access_token = token_data["access_token"]
        openid = token_data["openid"]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Token exchange failed: {str(e)}")

    # Step 3: 获取用户基本信息
    user_info_url = f"https://api.weixin.qq.com/sns/userinfo?access_token={access_token}&openid={openid}"

    try:
        user_res = requests.get(user_info_url)
        user_data = user_res.json()

        if "errcode" in user_data:
            raise HTTPException(
                status_code=400,
                detail=f"WeChat user API error: {user_data.get('errmsg')}",
            )

        # 提取关键用户信息
        uinfo = user.WxUserInfo(
            open_id=user_data.get("openid"),
            nickname=user_data.get("nickname"),
            avatar=user_data.get("headimgurl"),
            unionid=user_data.get("unionid"),
        )
        db.add(uinfo)
        db.commit()
        db.refresh(uinfo)

        token = generate_random_hex_str(TOKEN_LEN)
        user_infos[token] = uinfo

        # 重定向到前端并携带token（示例）
        return RedirectResponse(url=f"{state}?token={token}")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"User info fetch failed: {str(e)}")


@app.post("/api/wx/pay/callback")
async def wechat_pay_callback(wechatpay_timestamp: HeaderField,
                              wechatpay_nonce: HeaderField,
                              wechatpay_signature: HeaderField,
                              wx: deps.WxClient,
                              request: Request) -> Response:

    body = await request.body()
    if not client.CryptoHelper.verify(wx.sec, wechatpay_timestamp, wechatpay_nonce, wechatpay_signature, body.decode()):
        raise HTTPException(status_code=400, detail=json.dumps({
            "code": "FAIL",
            "message": "失败"
        }, ensure_ascii=False))

    print(body)
    return Response()


@app.get("/api/user/info")
async def user_info(
    authorization: Annotated[Union[str, None], Header()] = None,
) -> user.WxUserInfo:
    if authorization is None:
        raise HTTPException(status_code=401, detail=f"No authorization token")

    (auth_type, token) = authorization.split()
    if auth_type == "bearer" and token in user_infos.keys():
        return user_infos[token]

    raise HTTPException(status_code=401, detail="No authorization token")
