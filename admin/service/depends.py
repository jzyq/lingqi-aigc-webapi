from fastapi import Depends, Request, FastAPI, Header, HTTPException
from sqlalchemy import Engine
import redis.asyncio as redis
from . import session


def get_app(req: Request) -> FastAPI:
    return req.app


def get_db(app: FastAPI = Depends(get_app)) -> Engine:
    return app.state.db


def get_rdb(app: FastAPI = Depends(get_app)) -> redis.Redis:
    return app.state.rdb


async def get_session(
    rdb: redis.Redis = Depends(get_rdb),
    authorization: str | None = Header(default=None),
) -> session.Session:
    if not authorization:
        raise HTTPException(401, "need authorization")

    auth_type, auth_token = authorization.split(" ")
    if auth_type.lower() != "bearer":
        raise HTTPException(401, "authorization type not support")

    ses = await session.read_session(rdb, auth_token)
    if not ses:
        raise HTTPException(401, "need authorization")

    return ses
