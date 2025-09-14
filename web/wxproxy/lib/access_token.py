from dataio import config, errors
from datetime import datetime, timedelta
import httpx
from pydantic import BaseModel

_ENDPOINT = "https://api.weixin.qq.com/cgi-bin/token"


class _FetchAccessTokenRequest(BaseModel):
    grant_type: str = "client_credential"
    appid: str
    secret: str


class _FetchAccessTokenResponse(BaseModel):
    access_token: str
    expires_in: int


class AccessToken:

    async def __get_conf(self) -> config.wechat.HeavenAlbum:
        try:
            conf = await config.wechat.HeavenAlbum.get()
        except errors.NotExists:
            # TODO write oplogs
            raise

        return conf

    async def refresh_token(self) -> str:
        conf = await self.__get_conf()
        req = _FetchAccessTokenRequest(appid=conf.appid, secret=conf.secret)

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(_ENDPOINT, params=req.model_dump())
                resp.raise_for_status()
                response = _FetchAccessTokenResponse.model_validate_json(resp.content)

                conf.access_token = response.access_token
                conf.access_token_expires = datetime.now() + timedelta(
                    seconds=response.expires_in
                )
                await conf.save()
                return conf.access_token

            except httpx.HTTPError:
                # TODO write oplogs
                raise

    async def token(self) -> str:
        conf = await self.__get_conf()

        if conf.access_token and conf.access_token_expires:
            if datetime.now() < conf.access_token_expires:
                return conf.access_token

        return await self.refresh_token()
