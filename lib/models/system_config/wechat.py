from pydantic import BaseModel
from datetime import datetime
from .base import SystemConfig


class HeavenAlbum(BaseModel):
    cloud_env: str
    appid: str
    secret: str
    access_token: str | None = None
    access_token_expires: datetime | None = None


class Login(BaseModel):
    appid: str
    redirect_url: str


class WechatConfig(SystemConfig):
    heaven_album: HeavenAlbum | None = None
    login: Login | None = None
