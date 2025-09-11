from fastapi import FastAPI
from pydantic import BaseModel
from oss import init
from pymongo import AsyncMongoClient
from contextlib import asynccontextmanager
from .app import router


class Config(BaseModel):
    mongodb_url: str = "mongodb://localhost:27017/"


def make_app(conf: Config) -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        client = AsyncMongoClient(conf.mongodb_url)
        await init(client.aigc)
        yield

    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    return app
