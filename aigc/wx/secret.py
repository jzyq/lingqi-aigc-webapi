from pydantic import BaseModel
from ..config import WechatSecretConfig


class LoadWxSecertsError(Exception):
    pass


class WxSecrets(BaseModel):
    login_app_id: str
    app_id: str
    app_secret: str
    mch_id: str
    mch_cert_serial: str
    api_v3_pwd: str
    wxpay_pub_key: bytes
    apiclient_key: bytes


def must_load_secert(conf: WechatSecretConfig) -> WxSecrets:
    login_app_id: str
    app_id: str
    app_secret: str
    merchant_id: str
    merchant_cert_erial_no: str
    api_v3_pwd: str
    client_key: bytes
    wx_pub_key: bytes

    try:
        login_app_id = conf.login_id
        app_id = conf.app_id
        app_secret = conf.app_secret
        merchant_id = conf.mch_id
        merchant_cert_erial_no = conf.mch_cert_serial
        api_v3_pwd = conf.api_v3_pwd

        with open(conf.api_client_key_path, "rb") as fp:
            client_key = fp.read()

        with open(conf.pub_key_path, "rb") as fp:
            wx_pub_key = fp.read()

        return WxSecrets(
            login_app_id=login_app_id,
            app_id=app_id,
            app_secret=app_secret,
            mch_id=merchant_id,
            mch_cert_serial=merchant_cert_erial_no,
            apiclient_key=client_key,
            wxpay_pub_key=wx_pub_key,
            api_v3_pwd=api_v3_pwd,
        )
    except:
        raise LoadWxSecertsError("load wx secerts error, check secerts and key files")
