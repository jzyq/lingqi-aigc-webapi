from .access_token import PersistenceWxAccessToken
import httpx
from loguru import logger


class HeavenAlbum:

    __INVOKE_FUNC_URL = "https://api.weixin.qq.com/tcb/invokecloudfunction"

    def __init__(self, access_token: PersistenceWxAccessToken, env: str) -> None:
        self.__access_token = access_token
        self.__env = env

    async def update_task(
        self, tid: str, state: str, images: list[str] | None = None
    ) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url=self.__INVOKE_FUNC_URL,
                params={
                    "access_token": await self.__access_token.token,
                    "env": self.__env,
                    "name": "aigc",
                },
                json={
                    "func": "heaven_album:update_task",
                    "params": {"tid": tid, "images": images, "state": state},
                },
            )
