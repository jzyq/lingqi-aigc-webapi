from pydantic import BaseModel
from datetime import datetime, timedelta
import httpx
from loguru import logger
from persistence.sysconf import WechatConfig
from abc import ABC, abstractmethod


class AsyncAccessTokenManager(ABC):

    @property
    @abstractmethod
    async def token(self) -> str:
        pass


class WxAccessToken:

    __ENDPOINT = "https://api.weixin.qq.com/cgi-bin/token"

    class Token(BaseModel):
        access_token: str
        expires_in: int

    def __init__(self, appid: str, secret: str) -> None:
        self.appid = appid
        self.secret = secret
        self.__expires: datetime = datetime.now()
        self.__token: WxAccessToken.Token | None = None

        self.__params: dict[str, str] = {
            "grant_type": "client_credential",
            "appid": self.appid,
            "secret": self.secret,
        }

    def refresh(self) -> None:
        resp = httpx.get(self.__ENDPOINT, params=self.__params)
        self.__token = WxAccessToken.Token.model_validate_json(resp.content)
        self.__expires = datetime.now() + timedelta(seconds=self.__token.expires_in)
        logger.debug(
            f"refresh wx access token, new token {self.__token.access_token}, expires in {self.__token.expires_in}"
        )

    async def async_refresh(self) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(self.__ENDPOINT, params=self.__params)
            self.__token = WxAccessToken.Token.model_validate_json(resp.content)
            self.__expires = datetime.now() + timedelta(seconds=self.__token.expires_in)

    def __make_sure_token_valid(self) -> Token:
        if not self.__token:
            raise ValueError("need refresh token")
        if datetime.now() >= self.__expires:
            raise ValueError("token expired")
        return self.__token

    @property
    def token(self) -> str:
        tk = self.__make_sure_token_valid()
        return tk.access_token

    @property
    def expires_in(self) -> int:
        tk = self.__make_sure_token_valid()
        return tk.expires_in

    @property
    def expires(self) -> datetime:
        self.__make_sure_token_valid()
        return self.__expires

    def __str__(self) -> str:
        return self.token


class PersistenceWxAccessToken(AsyncAccessTokenManager):

    def __init__(self, appid: str, secret: str) -> None:
        self.__access_token = WxAccessToken(appid=appid, secret=secret)

    @property
    async def token(self) -> str:
        conf = await WechatConfig.all().first_or_none()
        if not conf:
            raise ValueError("no wechat config in persistence")

        if (
            conf.access_token
            and conf.access_token_expires
            and datetime.now() < conf.access_token_expires
        ):
            return conf.access_token

        await self.__access_token.async_refresh()
        conf.access_token = self.__access_token.token
        conf.access_token_expires = self.__access_token.expires
        await conf.save()

        return conf.access_token
