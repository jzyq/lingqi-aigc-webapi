from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):

    mode: Literal["dev", "prod"] = "prod"

    model_config = SettingsConfigDict(env_file=".env")

    api_host: str = "0.0.0.0"
    api_port: int = 80

    db_url: str = "mysql+mysqlconnector://aigc:q1w2e3r4@mysql:3306/aigc"

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0

    ui_base: str = "ui"

    superuser: str = "superadmin"
    superuser_password: str = "superq1w2e3r4"
