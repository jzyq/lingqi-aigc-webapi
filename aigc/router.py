from fastapi import APIRouter
from . import api


router = APIRouter(prefix="/api")

router.include_router(api.wx_router)
router.include_router(api.user_router)
router.include_router(api.payment_router)
router.mount("/infer", api.infer.app)
