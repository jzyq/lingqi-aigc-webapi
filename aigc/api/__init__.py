from . import wx, user, payment, infer, gallery, main
from . import dev  # type: ignore
from fastapi import APIRouter

router = APIRouter(prefix="/api")

router.include_router(wx.router)
router.include_router(user.router)
router.include_router(payment.router)
router.include_router(infer.router)
router.include_router(gallery.router)
router.include_router(main.router)
