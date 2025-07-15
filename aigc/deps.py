from typing import Annotated
from collections.abc import Iterator
from fastapi import Depends, Request, FastAPI, HTTPException, Header
from sqlmodel import Session
from sqlalchemy import Engine
import redis.asyncio as redis
from . import sessions, config, wx, models

from functools import cache


def get_db_file_path(conf: config.Config = Depends(config.get_config)) -> str:
    return conf.database.file


@cache
def get_db_engine(filepath: str = Depends(get_db_file_path)) -> Engine:
    return models.initialize_database_io(filepath)


def get_db_session(engine: Engine = Depends(get_db_engine)) -> Iterator[Session]:
    with Session(engine) as s:
        yield s


HeaderField = Annotated[str, Header()]


def set_rdb_deps(app: FastAPI, rdb: redis.Redis):
    app.state.rdb = rdb


def get_rdb(req: Request) -> redis.Redis:
    return req.app.state.rdb


def get_auth_token(authorization: HeaderField) -> str:
    auth_type, token = authorization.split(" ")
    if auth_type not in ["bearer", "Bearer"]:
        raise HTTPException(status_code=401, detail="no valid authorization to access.")
    return token


Rdb = Annotated[redis.Redis, Depends(get_rdb)]

AuthToken = Annotated[str, Depends(get_auth_token)]


async def get_user_session(rdb: Rdb, token: AuthToken) -> sessions.Session:
    ses = await sessions.get_session_or_none(rdb, token)
    if ses is None:
        raise HTTPException(status_code=401, detail="no valid authorization to access.")

    # Refersh session automaticly when have valid session.
    await sessions.refresh_session(rdb, token)
    return ses


UserSession = Annotated[sessions.Session, Depends(get_user_session)]


def get_wxclient(
    conf: config.Config = Depends(config.get_config),
) -> wx.client.WxClient:
    return wx.client.new_client(conf.wechat.secrets)


def get_main_page_data() -> models.mainpage.MainPageData:
    path = "mainpage/data.json"
    with open(path, 'r') as fp:
        data = models.mainpage.MainPageData.model_validate_json(fp.read())
    return data