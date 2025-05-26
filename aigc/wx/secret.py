from pydantic import BaseModel
import json


class LoadWxSecertsError(Exception):
    pass


class WxSecrets(BaseModel):
    login_app_id: str
    app_id: str
    app_secret: str
    mch_id: str
    mch_cert_serial: str
    wxpay_pub_key: bytes
    apiclient_key: bytes


def must_load_secert(secerts: str, apiclient_key: str, pub_key: str) -> WxSecrets:
    login_app_id: str
    app_id: str
    app_secret: str
    merchant_id: str
    merchant_cert_erial_no: str
    client_key: bytes
    wx_pub_key: bytes

    try:
        with open(secerts, 'r') as fp:
            data = json.load(fp)
            login_app_id = data['login_app_id']
            app_id = data['app_id']
            app_secret = data['app_secret']
            merchant_id = data['mch_id']
            merchant_cert_erial_no = data['mch_cert_serial']

        with open(apiclient_key, 'rb') as fp:
            client_key = fp.read()

        with open(pub_key, 'rb') as fp:
            wx_pub_key = fp.read()

        return WxSecrets(
            login_app_id=login_app_id,
            app_id=app_id, app_secret=app_secret, mch_id=merchant_id,
            mch_cert_serial=merchant_cert_erial_no, apiclient_key=client_key,
            wxpay_pub_key=wx_pub_key
        )
    except:
        raise LoadWxSecertsError(
            "load wx secerts error, check secerts and key files")
