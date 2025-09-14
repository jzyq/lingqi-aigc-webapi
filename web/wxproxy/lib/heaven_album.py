from .access_token import AccessToken
from dataio import config, errors
import httpx
from typing import Sequence

class HeavenAlbum:

    __INVOKE_FUNC_URL = "https://api.weixin.qq.com/tcb/invokecloudfunction"

    async def update_task(
        self, tid: str, state: str, images: Sequence[str] | None = None
    ) -> None:
        try:
            conf = await config.wechat.HeavenAlbum.get()
        except errors.NotExists:
            # TODO write oplogs
            raise

        access_token = AccessToken()

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url=self.__INVOKE_FUNC_URL,
                params={
                    "access_token": await access_token.token(),
                    "env": conf.cloud_env,
                    "name": "aigc",
                },
                json={
                    "func": "heaven_album:update_task",
                    "params": {"tid": tid, "images": images, "state": state},
                },
            )
