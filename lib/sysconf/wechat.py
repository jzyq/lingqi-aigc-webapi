from database.config import SystemConfigCategory as Category
from sqlalchemy import Engine
from pydantic import BaseModel
from .common import SysConfWithCategory


class Secrets(BaseModel):
    login_id: str
    app_id: str
    app_secret: str
    mch_id: str
    mch_cert_serial: str
    pub_key_id: str
    api_v3_pwd: str
    api_client_key: bytes
    pub_key: bytes


class Config:

    def __init__(self, db: Engine) -> None:
        self._sysconf = SysConfWithCategory(db, Category.wechat)

        self._secrets_name: str = "secrets"
        self._login_callback_name: str = "login_callback"
        self._payment_callback_name: str = "payment_callback"
        self._payment_expires_name: str = "payment_expires"

    @property
    def secrets(self) -> Secrets | None:
        value = self._sysconf.get(self._secrets_name)
        if not value:
            return None
        return Secrets.model_validate_json(value)

    @secrets.setter
    def secrets(self, secrets: Secrets) -> None:
        self._sysconf.set(self._secrets_name, secrets.model_dump_json())

    @property
    def login_redirect_url(self) -> str | None:
        return self._sysconf.get(self._login_callback_name)

    @login_redirect_url.setter
    def login_redirect_url(self, url: str) -> None:
        self._sysconf.set(self._login_callback_name, url)

    @property
    def payment_callback_url(self) -> str | None:
        return self._sysconf.get(self._payment_callback_name)

    @payment_callback_url.setter
    def payment_callback_url(self, url: str) -> None:
        return self._sysconf.set(self._payment_callback_name, url)

    @property
    def payment_expires(self) -> int | None:
        value = self._sysconf.get(self._payment_expires_name)
        if value:
            return int(value)
        return None

    @payment_expires.setter
    def payment_expires(self, seconds: int) -> None:
        self._sysconf.set(self._payment_expires_name, str(seconds))
