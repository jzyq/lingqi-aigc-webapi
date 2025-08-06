from . import wechat
from fastapi import APIRouter

router = APIRouter(prefix="/sysconf")

router.include_router(wechat.router)