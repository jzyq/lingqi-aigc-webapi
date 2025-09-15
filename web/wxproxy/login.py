from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/login")


class GetQRCodeLoginUrlRequest(BaseModel):
    pass


class GetQRCodeLoginUrlResponse(BaseModel):
    url: str


@router.get("/qrcode")
async def gen_qrcode_login_url(
    req: GetQRCodeLoginUrlRequest,
) -> GetQRCodeLoginUrlResponse:
    return GetQRCodeLoginUrlResponse(url="123")
