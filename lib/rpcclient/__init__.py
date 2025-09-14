from . import wechat
from pydantic import BaseModel


class Prefix(BaseModel):
    wechat: str = "/wechat"


_endpoint: str = "http://127.0.0.1:8000"
_prefix: Prefix | None = None


async def init(endpoint: str, prefix: Prefix | None) -> None:
    global _endpoint
    global _prefix

    _endpoint = endpoint
    _prefix = prefix


class Client:

    def __init__(
        self, endpoint: str | None = None, prefix: Prefix | None = None
    ) -> None:
        self.__endpoint = endpoint if endpoint else _endpoint
        self.__prefix = prefix if prefix else _prefix

    @property
    def wechat(self) -> wechat.Wechat:
        endpoint = self.__endpoint
        if self.__prefix:
            endpoint += self.__prefix.wechat
        return wechat.Wechat(endpoint)
