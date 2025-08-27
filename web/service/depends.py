from fastapi import Request, FastAPI, Depends
from typing import Annotated
import redis.asyncio as asyncredis


# Define dependices initlize functions.
class Initlization:

    @staticmethod
    def set_async_redis_connection_pool(
        app: FastAPI, conn_pool: asyncredis.ConnectionPool
    ):
        app.state.async_rdb_conn_pool = conn_pool


def __app(request: Request) -> FastAPI:
    return request.app


def __async_rdb_conn_pool(app: FastAPI = Depends(__app)) -> asyncredis.ConnectionPool:
    return app.state.async_rdb_conn_pool


# Define depends.
App = Annotated[FastAPI, Depends(__app)]
AsyncRedisConnectionPool = Annotated[
    asyncredis.ConnectionPool, Depends(__async_rdb_conn_pool)
]
