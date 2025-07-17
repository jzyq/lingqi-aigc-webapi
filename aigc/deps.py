from typing import Annotated
from collections.abc import Iterator
from fastapi import Depends, Request, FastAPI, HTTPException, Header
from sqlmodel import Session
from sqlalchemy import Engine
import redis.asyncio as redis
from . import infer_dispatch, sessions, config, wx, models, prompt_translate


def get_app(req: Request) -> FastAPI:
    return req.app


def get_db_engine(app: FastAPI = Depends(get_app)) -> Engine:
    return app.state.db


def get_db_session(engine: Engine = Depends(get_db_engine)) -> Iterator[Session]:
    with Session(engine) as s:
        yield s


HeaderField = Annotated[str, Header()]


def get_rdb(app: FastAPI = Depends(get_app)) -> redis.Redis:
    return app.state.rdb


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
    path = "mainpage/config.json"
    with open(path, "r") as fp:
        data = models.mainpage.MainPageData.model_validate_json(fp.read())
    return data


def get_translator(
    conf: config.Config = Depends(config.get_config),
) -> prompt_translate.ZhipuaiClient:
    return prompt_translate.ZhipuaiClient(conf.prompt_translate.api_key)


def get_inference_client(
    rdb: redis.Redis = Depends(get_rdb), db: Engine = Depends(get_db_engine)
) -> infer_dispatch.Client:
    return infer_dispatch.Client(rdb, db)
