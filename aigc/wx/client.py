from . import models, crypto
import json
import time
from urllib.parse import quote_plus
import httpx
from ..config import WechatSecretConfig


WX_MAIN_HOST = "https://api.mch.weixin.qq.com"

URL_OPEN_TRANSACTION = "/v3/pay/transactions/native"
URL_QUERY_TRANSACTION_BY_TRADE_NO = "/v3/pay/transactions/out-trade-no/{}"
URL_CLOSE_TRANSACTION = "/v3/pay/transactions/out-trade-no/{}/close"


WX_HEADER_SINGATURE = "Wechatpay-Signature"
WX_HEADER_TIMESTAMP = "Wechatpay-Timestamp"
WX_HEADER_NONCE = "Wechatpay-Nonce "


JSON_HEADER = {"Acctpt": "application/json", "Content-Type": "application/json"}


class CallError(Exception):

    def __init__(self, code: int, msg: str, *args: object) -> None:
        super().__init__(*args)
        self.code = code
        self.msg = msg

    def __str__(self) -> str:
        return f"errcode: {self.code}, errmsg: [{self.msg}]"


class VerifyError(Exception):
    pass


class CryptoHelper:

    @staticmethod
    def make_timestamp_str() -> str:
        return str(int(time.time()))

    @staticmethod
    def make_auth_str(
        sec: WechatSecretConfig, timestamp: str, nonce: str, sign: str
    ) -> str:
        auth_type = "WECHATPAY2-SHA256-RSA2048"
        return f'{auth_type} mchid="{sec.mch_id}",nonce_str="{nonce}",signature="{sign}",timestamp="{timestamp}",serial_no="{sec.mch_cert_serial}"'

    @staticmethod
    def signature(
        sec: WechatSecretConfig, method: str, url: str, body: str
    ) -> dict[str, str]:
        nonce = crypto.make_nonce_str()
        timestamp = CryptoHelper.make_timestamp_str()
        prepare_sign = f"{method}\n{url}\n{timestamp}\n{nonce}\n{body}\n"
        sign = crypto.sha256_with_rsa_sign(sec.api_client_key, prepare_sign.encode())
        auth = CryptoHelper.make_auth_str(sec, timestamp, nonce, sign.decode())
        return {"Authorization": auth}

    @staticmethod
    def verify(
        sec: WechatSecretConfig, timestamp: str, nonce: str, sign: str, data: str
    ) -> bool:
        data = f"{timestamp}\n{nonce}\n{data}\n"
        return crypto.sha256_with_rsa_verify(sec.pub_key, sign.encode(), data)


def new_client(secerts: WechatSecretConfig) -> "WxClient":
    return WxClient(secerts)


class WxClient:

    def __init__(self, sec: WechatSecretConfig) -> None:
        self.sec = sec

    async def open_transaction(self, order: models.Order) -> str:

        # Prepare request body, add appid and mchid into request data.
        request_body = order.model_dump(
            exclude_none=True, exclude_unset=True, by_alias=True
        )
        request_body.update(
            {
                "appid": self.sec.app_id,
                "mchid": self.sec.mch_id,
            }
        )
        body = json.dumps(request_body, ensure_ascii=False)

        (code, content) = await self.post(
            URL_OPEN_TRANSACTION, params=None, body=body.encode()
        )

        resp = json.loads(content)
        if code == 200:
            return resp["code_url"]
        else:
            print(content)
            # raise CallError(code=resp['errcode'], msg=resp['errmsg'])
            return ""

    async def query_transaction_by_out_trade_no(self, out_trade_no: str):
        url = URL_QUERY_TRANSACTION_BY_TRADE_NO.format(quote_plus(out_trade_no))
        params = {"mchid": self.sec.mch_id}

        (code, content) = await self.get(url, params=params, body=None)
        print(code)
        print(content.decode())

    async def close_transaction(self, out_trade_no: str):
        url = URL_CLOSE_TRANSACTION.format(quote_plus(out_trade_no))
        body = json.dumps({"mchid": self.sec.mch_id}, ensure_ascii=False)

        (code, content) = await self.post(url, params=None, body=body.encode())

        # expect statuc code == 204
        print(code)
        print(content)

    async def get(
        self,
        url: str,
        params: dict[str, str] | None,
        body: bytes | None,
        verify: bool = False,
    ) -> tuple[int, bytes]:
        if params is not None:
            params_str = "?" + "&".join(
                [f"{quote_plus(p)}={quote_plus(params[p])}" for p in params]
            )
        else:
            params_str = ""

        url = url + params_str

        auth_header = CryptoHelper.signature(
            self.sec,
            method="GET",
            url=url,
            body=body.decode() if body is not None else "",
        )
        auth_header.update(JSON_HEADER)

        async with httpx.AsyncClient() as client:
            resp = await client.request(
                "GET", url=WX_MAIN_HOST + url, content=body, headers=auth_header
            )

        if verify:
            sign = resp.headers.get(WX_HEADER_SINGATURE)
            timestamp = resp.headers.get(WX_HEADER_TIMESTAMP)
            nonce = resp.headers.get(WX_HEADER_NONCE)

            if (
                sign
                and timestamp
                and nonce
                and CryptoHelper.verify(
                    self.sec, timestamp, nonce, sign, resp.content.decode()
                )
            ):
                return (resp.status_code, resp.content)
            else:
                raise VerifyError()
        else:
            return (resp.status_code, resp.content)

    async def post(
        self,
        url: str,
        params: dict[str, str] | None,
        body: bytes | None,
        verify: bool = False,
    ) -> tuple[int, bytes]:
        if params is not None:
            params_str = "?" + "&".join(
                [f"{quote_plus(p)}={quote_plus(params[p])}" for p in params]
            )
        else:
            params_str = ""

        url = url + params_str

        auth_header = CryptoHelper.signature(
            self.sec,
            method="POST",
            url=url,
            body=body.decode() if body is not None else "",
        )
        auth_header.update(JSON_HEADER)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url=WX_MAIN_HOST + url, content=body, headers=auth_header
            )

        if verify:
            sign = resp.headers.get(WX_HEADER_SINGATURE)
            timestamp = resp.headers.get(WX_HEADER_TIMESTAMP)
            nonce = resp.headers.get(WX_HEADER_NONCE)

            if (
                sign
                and timestamp
                and nonce
                and CryptoHelper.verify(
                    self.sec, timestamp, nonce, sign, resp.content.decode()
                )
            ):
                return (resp.status_code, resp.content)
            else:
                raise VerifyError()
        else:
            return (resp.status_code, resp.content)

    def verify(self, timestamp: str, nonce: str, sign: str, data: str) -> bool:
        return CryptoHelper.verify(self.sec, timestamp, nonce, sign, data)

    def decrypt(self, ciphertext: str, nonce: str, associate: str) -> bytes:
        return crypto.decrypt_aes_256_gcm(
            self.sec.api_v3_pwd, ciphertext, nonce, associate
        )

    def get_qrcode_login_url(self, redirect_url: str, state: str) -> str:

        return (
            "https://open.weixin.qq.com/connect/qrconnect"
            + f"?appid={self.sec.login_id}"
            + f"&redirect_uri={redirect_url}"
            + "&response_type=code&scope=snsapi_login"
            + f"&state={state}"
            + "#wechat_redirect"
        )

    async def require_access_token(self, code: str) -> models.AccessToken:
        token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
        params = {
            "appid": self.sec.login_id,
            "secret": self.sec.app_secret,
            "code": code,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(token_url, params=params)
        if resp.status_code == 200:
            return models.AccessToken.model_validate_json(resp.content)

        err_data = json.loads(resp.content)
        raise CallError(code=err_data["errcode"], msg=err_data["errmsg"])

    async def fetch_user_info(self, openid: str, access_token: str) -> models.UserInfo:
        url = "https://api.weixin.qq.com/sns/userinfo"
        params = {"access_token": access_token, "openid": openid}

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
        if resp.status_code == 200:
            return models.UserInfo.model_validate_json(resp.content)

        err_data = json.loads(resp.content)
        raise CallError(code=err_data["errcode"], msg=err_data["errmsg"])
