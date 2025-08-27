from datetime import datetime
from beanie import Document, UnionDoc
import pymongo
from pydantic import BaseModel


class SysConfig(UnionDoc):
    class Settings:
        name = "sys_config"


class WechatConfig(Document):
    cloud_env: str
    appid: str
    secret: str

    access_token: str | None = None
    access_token_expires: datetime | None = None

    class Settings:
        name = "wechat"
        union_doc = SysConfig
        class_id = "category"
        indexes = [
            pymongo.IndexModel(
                [("category", pymongo.ASCENDING)],
                name="category_ascending",
                unique=True,
            )
        ]


class HeavenAlbumConf(BaseModel):
    model: str
    system_prompt: str


class ZhipuaiConfig(Document):
    apikey: str
    model: str
    translate_prompt: str
    heaven_album: HeavenAlbumConf

    class Settings:
        name = "zhipuai"
        union_doc = SysConfig
        class_id = "category"
        indexes = [
            pymongo.IndexModel(
                [("category", pymongo.ASCENDING)],
                name="category_ascending",
                unique=True,
            )
        ]


class InferenceEndpoint(BaseModel):
    replace_any: str
    replace_reference: str
    segment_any: str
    image_to_video: str
    edit_with_prompt: str


class InferenceConfig(Document):
    service_host: str
    endpoints: InferenceEndpoint

    class Settings:
        name = "inference"
        union_doc = SysConfig
        class_id = "category"
        indexes = [
            pymongo.IndexModel(
                [("category", pymongo.ASCENDING)],
                name="category_ascending",
                unique=True,
            )
        ]
