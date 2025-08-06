import secrets
import redis.asyncio as redis
from pydantic import BaseModel

TOKEN_LEN = 8


class Session(BaseModel):
    username: str


async def read_session(rdb: redis.Redis, token: str) -> Session | None:
    data = await rdb.get(f"aigc:admin:session:{token}")
    if not data:
        return None
    return Session.model_validate_json(data)


async def create_session(rdb: redis.Redis, user: str) -> str:
    token = secrets.token_hex(TOKEN_LEN)
    ses = Session(username=user)

    await rdb.set(f"aigc:admin:session:{token}", ses.model_dump_json(), ex=3600)

    return token
