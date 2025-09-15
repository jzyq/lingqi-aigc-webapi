from beanie import init_beanie, Document
from pydantic import BaseModel
from pymongo import IndexModel, ASCENDING
from pymongo.asynchronous.database import AsyncDatabase

from datetime import datetime


async def init(db: AsyncDatabase) -> None:
    await init_beanie(db, document_models=[SystemConfig, WechatConfig])


class SystemConfig(Document):
    class Settings:
        name = "system_config"
        is_root = True
        class_id = "category"
        indexes = [IndexModel([("category", ASCENDING)], unique=True)]


class HeavenAlbum(BaseModel):
    cloud_env: str
    appid: str
    secret: str
    access_token: str | None = None
    access_token_expires: datetime | None = None


class WechatLogin(BaseModel):
    appid: str
    redirect_url: str


class WechatConfig(SystemConfig):
    heaven_album: HeavenAlbum | None = None
    login: WechatLogin | None = None
