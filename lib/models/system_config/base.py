from beanie import Document
from pymongo import IndexModel, ASCENDING


class SystemConfig(Document):
    class Settings:
        name = "system_config"
        is_root = True
        class_id = "category"
        indexes = [IndexModel([("category", ASCENDING)], unique=True)]
