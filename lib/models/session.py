from beanie import Document
from datetime import datetime
from pymongo import IndexModel
from pymongo.asynchronous.database import AsyncDatabase


async def init(db: AsyncDatabase) -> None:
    from beanie import init_beanie

    await init_beanie(db, document_models=[Session])


class Session(Document):
    uid: str
    nickname: str
    login_time: datetime
    update_time: datetime
    expires: datetime
    expire_in: int

    class Settings:
        name = "sessions"
        indexes = [
            IndexModel("expires", expireAfterSeconds=0),
            IndexModel("uid", unique=True),
        ]
