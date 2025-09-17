from typing import Annotated
from collections.abc import Iterator
from fastapi import Depends, Request, FastAPI, HTTPException, Header
from sqlmodel import Session
from sqlalchemy import Engine
from . import infer_dispatch, sessions, config, prompt_translate
import sysconf
import wechat


def get_app(req: Request) -> FastAPI:
    return req.app


def get_db_engine(app: FastAPI = Depends(get_app)) -> Engine:
    return app.state.db


def get_db_session(engine: Engine = Depends(get_db_engine)) -> Iterator[Session]:
    with Session(engine) as s:
        yield s


HeaderField = Annotated[str, Header()]


def get_auth_token(authorization: HeaderField) -> str:
    auth_type, token = authorization.split(" ")
    if auth_type not in ["bearer", "Bearer"]:
        raise HTTPException(status_code=401, detail="no valid authorization to access.")
    return token


AuthToken = Annotated[str, Depends(get_auth_token)]


async def get_user_session(token: AuthToken) -> sessions.Session:
    ses = await sessions.get_session_or_none(token)
    if ses is None:
        raise HTTPException(status_code=401, detail="no valid authorization to access.")

    # Refersh session automaticly when have valid session.
    await sessions.refresh_session(token)
    return ses


UserSession = Annotated[sessions.Session, Depends(get_user_session)]


def get_wechat_conf(db: Engine = Depends(get_db_engine)) -> sysconf.wechat.Config:
    return sysconf.wechat.Config(db)


def get_wxclient(
    conf: sysconf.wechat.Config = Depends(get_wechat_conf),
) -> wechat.client.WxClient:
    secrets = conf.secrets
    if not secrets:
        raise HTTPException(500, "wechat secrets must be set property first")
    return wechat.client.new_client(secrets)


def get_translator(
    conf: config.Config = Depends(config.get_config),
) -> prompt_translate.ZhipuaiClient:
    return prompt_translate.ZhipuaiClient(conf.prompt_translate.api_key)


def get_inference_client(db: Engine = Depends(get_db_engine)) -> infer_dispatch.Client:
    return infer_dispatch.Client(db)
