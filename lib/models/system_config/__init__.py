from beanie import init_beanie
from pymongo.asynchronous.database import AsyncDatabase
from . import base, wechat


async def init(db: AsyncDatabase) -> None:
    await init_beanie(db, document_models=[base.SystemConfig, wechat.WechatConfig])
