from fastapi import APIRouter, Depends
from pydantic import BaseModel
import redis.asyncio
from sqlmodel import Session, select
from .. import deps, models, sessions

router = APIRouter()


class APIResponse(BaseModel):
    code: int = 0
    msg: str = "ok"


class RegisterUserRequest(BaseModel):
    username: str
    nickname: str


class UserLoginRequest(BaseModel):
    username: str


# Add some API for dev
@router.post("/user/register")
async def register_user(
    req: RegisterUserRequest, dbsession: Session = Depends(deps.get_db_session)
) -> APIResponse:

    u = models.db.User(
        username=req.username, nickname=req.nickname, avatar="avatar.jpg"
    )
    dbsession.add(u)
    dbsession.commit()
    dbsession.refresh(u)

    assert u.id

    s = models.db.MagicPointSubscription(
        uid=u.id, stype=models.db.SubscriptionType.trail, init=1000, remains=1000
    )
    dbsession.add(s)
    dbsession.commit()

    return APIResponse()


# Login API to generate user session.
@router.post("/user/login")
async def user_login(
    req: UserLoginRequest,
    dbsession: Session = Depends(deps.get_db_session),
    rdb: redis.asyncio.Redis = Depends(deps.get_rdb),
) -> APIResponse:
    query = select(models.db.User).where(models.db.User.username == req.username)
    u = dbsession.exec(query).one_or_none()
    if u is None:
        return APIResponse(code=1, msg="no such user")
    assert u.id

    tk = await sessions.create_new_session(rdb, u.id, u.nickname)
    return APIResponse(msg=tk)


# Fake infer API
@router.post("/infer/{type}")
async def fake_inference(type: str) -> APIResponse:
    return APIResponse(msg=f"infer complete, your infer type is {type}")
