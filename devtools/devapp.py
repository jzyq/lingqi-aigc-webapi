from fastapi import FastAPI, Depends
from aigc import config, deps, api, models, sessions
from sqlmodel import create_engine, SQLModel, Session, select
from sqlalchemy.pool import StaticPool
from fakeredis import FakeAsyncRedis
from pydantic import BaseModel
import redis.asyncio as redis

# Make test config
conf = config.Config()
conf.magic_points.subscriptions = [
    config.MagicPointSubscription(price=100, month=1, points=1000)
]
conf.infer.base = "http://localhost:8000/dev/infer"

# Make test database, use in memory database.
connect_args = {"check_same_thread": False}
engine = create_engine("sqlite://", connect_args=connect_args, poolclass=StaticPool)
SQLModel.metadata.create_all(engine)


# Make test redis.
rdb = FakeAsyncRedis()


# Setup dev app.
app = FastAPI()

app.dependency_overrides[config.get_config] = lambda: conf
app.dependency_overrides[deps.get_db_engine] = lambda: engine
app.dependency_overrides[deps.get_rdb] = lambda: rdb

app.include_router(api.main.router)
app.include_router(api.infer.router)
app.include_router(api.user.router)
app.include_router(api.gallery.router)


class APIResponse(BaseModel):
    code: int = 0
    msg: str = "ok"


class RegisterUserRequest(BaseModel):
    username: str
    nickname: str


class UserLoginRequest(BaseModel):
    username: str


# Add some API for dev
@app.post("/dev/user/register")
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
@app.post("/dev/user/login")
async def user_login(
    req: UserLoginRequest,
    dbsession: Session = Depends(deps.get_db_session),
    rdb: redis.Redis = Depends(deps.get_rdb),
) -> APIResponse:
    query = select(models.db.User).where(models.db.User.username == req.username)
    u = dbsession.exec(query).one_or_none()
    if u is None:
        return APIResponse(code=1, msg="no such user")
    assert u.id

    tk = await sessions.create_new_session(rdb, u.id, u.nickname)
    return APIResponse(msg=tk)


# Fake infer API
@app.post("/dev/infer/{type}")
async def fake_inference(type: str) -> APIResponse:
    return APIResponse(msg=f"infer complete, your infer type is {type}")
