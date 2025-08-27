from .access_token import AsyncAccessTokenManager
import httpx
import io
from pydantic import BaseModel
from loguru import logger


class PreUploadData(BaseModel):
    errcode: int
    errmsg: str
    url: str
    token: str
    authorization: str
    file_id: str
    cos_file_id: str


class UploadError(Exception):
    pass


class WxCloudStorage:

    def __init__(self, access_token: AsyncAccessTokenManager, env: str) -> None:
        self.__access_token = access_token
        self.__cloud_env = env

    async def upload(self, filename: str, buf: io.BufferedIOBase) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.weixin.qq.com/tcb/uploadfile",
                params={
                    "access_token": await self.__access_token.token,
                },
                json={"env": self.__cloud_env, "path": filename},
            )
            upload_data = PreUploadData.model_validate_json(resp.content)
            logger.debug(f"pre upload data:\n{upload_data}")

            resp = await client.post(
                url=upload_data.url,
                files={
                    "key": filename,
                    "Signature": upload_data.authorization,
                    "x-cos-security-token": upload_data.token,
                    "x-cos-meta-fileid": upload_data.cos_file_id,
                    "file": buf.read(),
                },
            )
            if resp.status_code != 204:
                logger.error(
                    f"upload file {filename} failed, error message:\n{resp.text}"
                )
                raise UploadError(resp.text)
            else:
                logger.debug(
                    f"upload file {filename} ok, file id {upload_data.file_id}"
                )
                return upload_data.file_id
