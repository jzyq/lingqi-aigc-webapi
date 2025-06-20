from fastapi import APIRouter
from . import deps, models
from sqlmodel import select
from datetime import datetime

router = APIRouter(prefix="/user")


@router.get("/info")
async def user_info(
    ses: deps.UserSession,
    db: deps.Database,
) -> models.user.GetUserInfoResponse:
    userinfo = db.get_one(models.db.User, ses.uid)
    subscription = db.exec(
        select(models.db.MagicPointSubscription)
        .where(models.db.MagicPointSubscription.uid == ses.uid)
        .where(models.db.MagicPointSubscription.expired == False)
    ).all()

    # Subscription should have only one.
    expires_in: datetime | None = None
    point_in_today: int = 0
    is_member = False
    for s in subscription:
        if s.stype == models.db.SubscriptionType.subscription:
            expires_in = s.expires_in
            is_member = True
        point_in_today += s.remains

    return models.user.GetUserInfoResponse(
        username=userinfo.username,
        nickname=userinfo.nickname,
        avatar=userinfo.avatar,
        point=point_in_today,
        expires_in=expires_in,
        is_member=is_member,
    )
