import asyncio
import requests
from . import models, secret, crypto
import json
import time

WX_MAIN_HOST = "https://api.mch.weixin.qq.com"
URL_PREPARE_TRANSACTION = "/v3/pay/transactions/native"


def new_client(secerts: secret.WxSecrets) -> 'WxClient':
    return WxClient(secerts)


class WxClient:

    def __init__(self, sec: secret.WxSecrets) -> None:
        self.sec = sec

    async def prepare_order(self, order: models.Order) -> str:

        # Prepare request body, add appid and mchid into request data.
        request_body = order.model_dump(
            exclude_none=True, exclude_unset=True, by_alias=True)
        request_body.update({
            "appid": self.sec.app_id,
            "mchid": self.sec.mch_id,
        })
        body = json.dumps(request_body, ensure_ascii=False)

        # Sign request and setup header.
        auth = self._signature_request("POST", URL_PREPARE_TRANSACTION, body)
        headers = self._make_header(auth)

        # send req.
        url = WX_MAIN_HOST + URL_PREPARE_TRANSACTION
        resp = await asyncio.to_thread(requests.post, url, data=body.encode(), headers=headers)
        if resp.status_code != 200:
            print(resp.status_code)
            print(resp.json())
            return ""

        data = resp.json()
        return data["code_url"]

    def _signature_request(self, method: str, url: str, body: str) -> str:
        nonce = crypto.make_nonce_str()
        timestamp = self._timestamp_str()

        prepare_sign = f"{method}\n{url}\n{timestamp}\n{nonce}\n{body}\n"
        sign = crypto.sha256_with_rsa_sign(
            self.sec.apiclient_key, prepare_sign.encode())

        auth = self._make_authorization(timestamp, nonce, sign)

        return auth

    def _make_header(self, auth: str) -> dict[str, str]:
        return {
            "Authorization": auth,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def _make_authorization(self, timestamp: str, nonce: str, signature: bytes) -> str:
        auth_type = "WECHATPAY2-SHA256-RSA2048"
        return f'{auth_type} mchid="{self.sec.mch_id}",nonce_str="{nonce}",signature="{signature.decode()}",timestamp="{timestamp}",serial_no="{self.sec.mch_cert_serial}"'

    def _timestamp_str(self) -> str:
        return str(int(time.time()))
