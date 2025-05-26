from fastapi import APIRouter
from . import deps, models

router = APIRouter(prefix="/user")


@router.get("/info")
async def user_info(
    ses: deps.UserSession,
    db: deps.Database,
) -> models.user.User:
    user_info = db.get(models.user.User, ses.uid)
    assert user_info is not None
    return user_info
