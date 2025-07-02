from fastapi import APIRouter
from . import sync_infer, async_infer

router = APIRouter()
router.include_router(sync_infer.router)
router.include_router(async_infer.router)
