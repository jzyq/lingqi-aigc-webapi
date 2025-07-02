from fastapi import APIRouter
from . import api


router = APIRouter(prefix="/api")

router.include_router(api.wx.router)
router.include_router(api.user.router)
router.include_router(api.payment.router)
router.include_router(api.infer.router)