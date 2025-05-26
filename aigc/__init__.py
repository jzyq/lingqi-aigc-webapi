from fastapi import APIRouter
from . import wx_api


router = APIRouter(prefix="/api")

router.include_router(wx_api.router)