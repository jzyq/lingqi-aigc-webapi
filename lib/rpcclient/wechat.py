from typing import BinaryIO
import httpx
from . import errors
from enum import StrEnum
from typing import Sequence


class HeavenAlbumTaskState(StrEnum):
    error = "error"


class Wechat:

    def __init__(self, endpoint: str) -> None:
        self.__endpoint = endpoint

    async def upload_file_to_cloud(
        self, filename: str, content_type: str, data: BinaryIO
    ) -> str:
        url = self.__endpoint + "/cloud/uploadfile"
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    url, files={"file": (filename, data, content_type)}
                )
                resp.raise_for_status()
                return resp.json()["file_id"]
            except httpx.HTTPError as exc:
                raise errors.CallError(
                    f"call wechat rpc: upload file to cloud failed, detail: {str(exc)}"
                ) from exc

    async def update_heaven_album_task_state(
        self, tid: str, state: HeavenAlbumTaskState, images: Sequence[str] | None = None
    ) -> None:
        url = self.__endpoint + "/rpc/heaven_album/task/state"
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    url, json={"tid": tid, "state": str(state), "images": images}
                )
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise errors.CallError(
                    f"call wechat rpc: update heaven album task state failed, detail: {str(exc)}"
                ) from exc

    async def generate_login_qrcode_url(self, redirect_url: str, state: str) -> str:
        url = self.__endpoint + "/login/qrcode"
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    url, params={"redirect_url": redirect_url, "state": state}
                )
                resp.raise_for_status()
                return resp.json()["url"]
            except httpx.HTTPError as exc:
                raise errors.CallError(
                    f"call wechat rpc: generate login qrcode url failed, detail: {str(exc)}"
                ) from exc
