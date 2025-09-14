from .access_token import AccessToken
import httpx
from pydantic import BaseModel
from loguru import logger
from dataio import config, errors
from typing import BinaryIO


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


class WechatOSS:

    async def upload(self, filename: str, buf: BinaryIO) -> str:
        try:
            conf = await config.wechat.HeavenAlbum.get()
        except errors.NotExists:
            # TODO: write oplogs
            raise

        access_token = AccessToken()

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.weixin.qq.com/tcb/uploadfile",
                params={
                    "access_token": await access_token.token(),
                },
                json={"env": conf.cloud_env, "path": filename},
            )
            upload_data = PreUploadData.model_validate_json(resp.content)
            logger.trace(f"pre upload data:\n{upload_data}")

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
