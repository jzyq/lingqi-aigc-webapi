from pymongo import AsyncMongoClient
from beanie import init_beanie
from . import sysconf


async def init_presistence(client: AsyncMongoClient):
    await init_beanie(
        database=client["aigc"],
        document_models=[
            sysconf.SysConfig,
            sysconf.WechatConfig,
            sysconf.ZhipuaiConfig,
            sysconf.InferenceConfig
        ],
    )
