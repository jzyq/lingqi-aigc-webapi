from fastapi import APIRouter, UploadFile
from pydantic import BaseModel
from .lib.oss import WechatOSS
import secrets


class UploadFileResponse(BaseModel):
    file_id: str


router = APIRouter(prefix="/cloud")


@router.post("/uploadfile")
async def upload_file(file: UploadFile) -> UploadFileResponse:
    client = WechatOSS()
    fid = await client.upload(
        file.filename if file.filename else secrets.token_hex(12), file.file
    )
    return UploadFileResponse(file_id=fid)
