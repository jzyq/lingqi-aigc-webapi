import redis.asyncio as redis
import random
from pydantic import BaseModel
from datetime import datetime, timedelta

from . import config


random.seed()

TOKEN_LEN = 16
SESSION_KEY = "aigc::ses::{}"
UID_SESSION_MAP_KEY = "aigc::uid-to-ses"


class Session(BaseModel):
    uid: int
    nickname: str
    login_time: datetime
    expires: datetime


def generate_new_token(k: int) -> str:
    seq = random.choices("0123456789abcdef", k=k)
    return "".join(seq)


async def create_new_session(rdb: redis.Redis, uid: int, nickname: str) -> str:
    dt = datetime.now()
    ttl = config.Config().web.session_ttl
    session = Session(
        uid=uid, nickname=nickname, login_time=dt, expires=dt + timedelta(seconds=ttl)
    )
    token = generate_new_token(TOKEN_LEN)

    p = rdb.pipeline()
    await p.set(SESSION_KEY.format(token), session.model_dump_json(), ex=ttl)
    p.hset(name=UID_SESSION_MAP_KEY, key=str(uid), value=token)  # type: ignore
    await p.execute()

    return token


async def get_session_or_none(rdb: redis.Redis, token: str) -> Session | None:
    resp = await rdb.get(SESSION_KEY.format(token))
    return resp if resp is None else Session.model_validate_json(resp)


async def delete_session(rdb: redis.Redis, token: str):
    p = rdb.pipeline()
    await p.delete(SESSION_KEY.format(token))
    p.hdel(UID_SESSION_MAP_KEY, token)
    await p.execute()


async def refresh_session(rdb: redis.Redis, token: str):
    ses = await get_session_or_none(rdb, token)
    if ses is None:
        return

    ttl = config.Config().web.session_ttl
    ses.expires = datetime.now() + timedelta(seconds=ttl)
    await rdb.set(SESSION_KEY.format(token), ses.model_dump_json(), ex=ttl)


async def find_session_by_uid(rdb: redis.Redis, uid: int) -> tuple[str, Session] | None:
    token = await rdb.hget(UID_SESSION_MAP_KEY, str(uid))  # type: ignore
    if not isinstance(token, str):
        return None

    resp = await rdb.get(SESSION_KEY.format(token))
    return None if resp is None else (token, Session.model_validate_json(resp))
