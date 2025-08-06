from fastapi import APIRouter, Depends
from ... import depends
from ...models import APIResponse
from sqlalchemy import Engine
import sysconf
from pydantic import BaseModel


class SetUrlReq(BaseModel):
    url: str


class SetIntReq(BaseModel):
    val: int


router = APIRouter(prefix="/wechat", dependencies=[Depends(depends.get_session)])


@router.get("/secrets", response_model=APIResponse, response_model_exclude_none=True)
async def get_secrets(db: Engine = Depends(depends.get_db)) -> APIResponse:
    secrets = sysconf.wechat.Config(db).secrets

    if secrets:
        return APIResponse(data=secrets)
    else:
        return APIResponse(code=1, msg="secrets not setup.")


@router.post("/secrets", response_model=APIResponse, response_model_exclude_none=True)
async def set_secrets(
    secrets: sysconf.wechat.Secrets, db: Engine = Depends(depends.get_db)
) -> APIResponse:

    conf = sysconf.wechat.Config(db)
    conf.secrets = secrets
    return APIResponse()


@router.get(
    "/login_callback", response_model=APIResponse, response_model_exclude_none=True
)
async def get_login_callback(db: Engine = Depends(depends.get_db)) -> APIResponse:
    callback = sysconf.wechat.Config(db).login_redirect_url
    if callback:
        return APIResponse(data={"url": callback})
    else:
        return APIResponse(code=1, msg="wechat login callback url not setup")


@router.post("/login_callback")
async def set_login_callback(
    req: SetUrlReq, db: Engine = Depends(depends.get_db)
) -> APIResponse:
    conf = sysconf.wechat.Config(db)
    conf.login_redirect_url = req.url
    return APIResponse()


@router.get(
    "/payment_callback", response_model=APIResponse, response_model_exclude_none=True
)
async def get_payment_callback(db: Engine = Depends(depends.get_db)) -> APIResponse:
    callback = sysconf.wechat.Config(db).payment_callback_url
    if callback:
        return APIResponse(data={"url": callback})
    else:
        return APIResponse(code=1, msg="wechat login callback url not setup")


@router.post("/payment_callback")
async def set_payment_callback(
    req: SetUrlReq, db: Engine = Depends(depends.get_db)
) -> APIResponse:
    conf = sysconf.wechat.Config(db)
    conf.payment_callback_url = req.url
    return APIResponse()


@router.get(
    "/payment_expires", response_model=APIResponse, response_model_exclude_none=True
)
async def get_payment_expires(db: Engine = Depends(depends.get_db)) -> APIResponse:
    seconds = sysconf.wechat.Config(db).payment_expires
    if seconds:
        return APIResponse(data={"seconds": seconds})
    else:
        return APIResponse(code=1, msg="wechat login callback url not setup")


@router.post("/payment_expires")
async def set_payment_expires(
    req: SetIntReq, db: Engine = Depends(depends.get_db)
) -> APIResponse:
    conf = sysconf.wechat.Config(db)
    conf.payment_expires = req.val
    return APIResponse()
