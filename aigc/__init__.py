from fastapi import APIRouter
from . import wx_api, user, payment


router = APIRouter(prefix="/api")

router.include_router(wx_api.router)
router.include_router(user.router)
router.include_router(payment.router)
