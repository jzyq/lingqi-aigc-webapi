from fastapi import APIRouter
from .. import deps, models
from dataio import users

router = APIRouter(prefix="/user")


@router.get("/info")
async def user_info(
    ses: deps.UserSession,
) -> models.user.GetUserInfoResponse:
    uinfo = await users.UserInfo.get(ses.uid)
    return models.user.GetUserInfoResponse(
        username=uinfo.username,
        nickname=uinfo.nickname,
        avatar=uinfo.avatar,
        point=await uinfo.remain_point(),
        is_member=await uinfo.is_member(),
        expires_in=await uinfo.member_expires(),
    )
