from pydantic import BaseModel
from datetime import datetime
from models.system_config import wechat
from .. import errors


class HeavenAlbum(BaseModel):
    cloud_env: str
    appid: str
    secret: str
    access_token: str | None = None
    access_token_expires: datetime | None = None

    @staticmethod
    async def get() -> "HeavenAlbum":
        res = await wechat.WechatConfig.find_one()

        if not res or not res.heaven_album:
            raise errors.NotExists("wechat heaven album config not exists")

        ha = HeavenAlbum(
            cloud_env=res.heaven_album.cloud_env,
            appid=res.heaven_album.appid,
            secret=res.heaven_album.secret,
            access_token=res.heaven_album.access_token,
            access_token_expires=res.heaven_album.access_token_expires,
        )

        return ha

    async def save(self) -> None:
        ha = wechat.HeavenAlbum(
            cloud_env=self.cloud_env,
            appid=self.appid,
            secret=self.secret,
            access_token=self.access_token,
            access_token_expires=self.access_token_expires,
        )

        conf = await wechat.WechatConfig.find_one()
        if not conf:
            conf = wechat.WechatConfig(heaven_album=ha)
        else:
            conf.heaven_album = ha

        await conf.save()


class Login(BaseModel):
    appid: str
    redirect_url: str

    @staticmethod
    async def get() -> "Login":
        res = await wechat.WechatConfig.find_one()
        if not res or not res.login:
            raise errors.NotExists("wechat login config not exists")

        return Login(
            appid=res.login.appid,
            redirect_url=res.login.redirect_url,
        )

    async def save(self) -> None:
        login = wechat.Login(appid=self.appid, redirect_url=self.redirect_url)

        conf = await wechat.WechatConfig.find_one()
        if not conf:
            conf = wechat.WechatConfig(login=login)
        else:
            conf.login = login
        await conf.save()
