from typing import Annotated, Generator
from fastapi import Depends, Request, FastAPI, HTTPException
from sqlmodel import Session
from .wx import secret, client
from sqlalchemy import Engine
import redis.asyncio as redis
from . import common, sessions, config, ai

from .async_task_manager import AsyncTaskManager
from functools import cache
from .models.infer import replace
from .config import WechatSecretConfig


def set_db_session_deps(app: FastAPI, engine: Engine):
    app.state.engine = engine


def set_wx_client_deps(app: FastAPI, conf: WechatSecretConfig):
    s = secret.must_load_secert(conf)
    wx_client = client.new_client(secerts=s)
    app.state.wx_client = wx_client


def set_rdb_deps(app: FastAPI, rdb: redis.Redis):
    app.state.rdb = rdb


def get_session(req: Request) -> Generator[Session, None, None]:
    with Session(req.app.state.engine) as s:
        yield s


def get_wx_client(req: Request) -> client.WxClient:
    return req.app.state.wx_client


def get_rdb(req: Request) -> redis.Redis:
    return req.app.state.rdb


def get_auth_token(authorization: common.HeaderField) -> str:
    auth_type, token = authorization.split(" ")
    if auth_type != "bearer" or token == "":
        raise HTTPException(status_code=401, detail="no valid authorization to access.")
    return token


def get_subscriptions_plan() -> list[config.MagicPointSubscription]:
    conf = config.MagicPointConfig()
    return conf.subscriptions


Database = Annotated[Session, Depends(get_session)]

WxClient = Annotated[client.WxClient, Depends(get_wx_client)]

Rdb = Annotated[redis.Redis, Depends(get_rdb)]

AuthToken = Annotated[str, Depends(get_auth_token)]

SubscriptionPlan = Annotated[
    list[config.MagicPointSubscription], Depends(get_subscriptions_plan)
]


async def get_user_session(rdb: Rdb, token: AuthToken) -> sessions.Session:
    ses = await sessions.get_session_or_none(rdb, token)
    if ses is None:
        raise HTTPException(status_code=401, detail="no valid authorization to access.")
    return ses


UserSession = Annotated[sessions.Session, Depends(get_user_session)]


# For infer replace with any async task manager.
@cache
def get_replace_async_task_manager() -> (
    AsyncTaskManager[replace.Request, replace.Response]
):
    async def proxy(uid: int, tid: str, req: replace.Request) -> replace.Response:
        return await ai.image.replace_with_any("", uid, tid, req)

    mgr = AsyncTaskManager[replace.Request, replace.Response](1, proxy)
    return mgr


ReplaceTasks = Annotated[
    AsyncTaskManager[replace.Request, replace.Response],
    Depends(get_replace_async_task_manager),
]

def get_conf() -> config.Config:
    return config.Config()

Config = Annotated[config.Config, Depends(get_conf)]
