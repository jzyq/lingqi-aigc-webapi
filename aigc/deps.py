from typing import Annotated, Generator
from fastapi import Depends, Request, FastAPI
from sqlmodel import Session
from .wx import secret, client
from sqlalchemy import Engine


def _get_session(req: Request) -> Generator[Session, None, None]:
    with Session(req.app.state.engine) as s:
        yield s


def _get_wx_client(req: Request) -> client.WxClient:
    return req.app.state.wx_client


DBSession = Annotated[Session, Depends(_get_session)]

WxClient = Annotated[client.WxClient, Depends(_get_wx_client)]


def set_db_session_deps(app: FastAPI, engine: Engine):
    app.state.engine = engine


def set_wx_client_deps(app: FastAPI, secret: secret.WxSecrets):
    wx_client = client.new_client(secerts=secret)
    app.state.wx_client = wx_client
