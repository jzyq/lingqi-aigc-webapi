import tomllib
from functools import cache
from dataclasses import dataclass, field
from typing import Any, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env")

    mode: Literal["prod", "dev"] = "prod"

    api_host: str = "0.0.0.0"
    api_port: int = 80

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0

    db_url: str = "mysql+mysqlconnector://aigc:q1w2e3r4@mysql:3306/aigc"

    storage_endpoint: str = "minio:9000"
    storage_user: str = "minioadmin"
    storage_password: str = "minioadmin"

    refresh_mainpage: bool = True

    mongodb_url: str = "mongodb://localhost:27017/"


@dataclass
class MagicPointSubscription:
    price: int
    month: int
    points: int

    @staticmethod
    def load(toml: dict[str, Any]) -> "MagicPointSubscription":
        return MagicPointSubscription(
            price=int(toml["price"]),
            month=int(toml["month"]),
            points=int(toml["points"]),
        )


@dataclass
class MagicPointConfig:
    trail_free_point: int = 30
    subscriptions: list[MagicPointSubscription] = field(
        default_factory=lambda: [
            MagicPointSubscription(price=9900, month=1, points=1000),
            MagicPointSubscription(price=29900, month=12, points=1000),
        ]
    )

    @staticmethod
    def load(toml: dict[str, Any]) -> "MagicPointConfig":
        return MagicPointConfig(
            trail_free_point=int(toml["trail_free_point"]),
            subscriptions=[
                MagicPointSubscription.load(t) for t in toml["subscriptions"]
            ],
        )


@dataclass
class InferConfig:
    long_poll_timeout: int = 30

    base: str = "http://localhost:8991"
    replace_any: str = "/replace_any"
    replace_reference: str = "/replace_with_reference"
    segment_any: str = "/segment_any"
    image_to_video: str = "/image_to_video"
    edit_with_prompt: str = "/edit_with_prompt"

    @staticmethod
    def load(toml: dict[str, Any]) -> "InferConfig":
        return InferConfig(
            base=toml["base"],
            long_poll_timeout=int(toml["long_poll_timeout"]),
            replace_any=toml["replace_any"],
            replace_reference=toml["replace_reference"],
            segment_any=toml["segment_any"],
            image_to_video=toml["image_to_video"],
            edit_with_prompt=toml["edit_with_prompt"],
        )


@dataclass
class PromptTranslate:
    api_key: str = ""

    @staticmethod
    def load(toml: dict[str, Any]) -> "PromptTranslate":
        return PromptTranslate(api_key=toml["api_key"])


@dataclass
class RemoteConfig:
    app_id: str = ""
    secret: str = ""
    bitable_id: str = ""

    @staticmethod
    def load(toml: dict[str, Any]) -> "RemoteConfig":
        return RemoteConfig(
            app_id=toml["app_id"], secret=toml["secret"], bitable_id=toml["bitable_id"]
        )


# Just read this config when needed.
@dataclass
class Config:
    magic_points: MagicPointConfig = field(default_factory=MagicPointConfig)
    infer: InferConfig = field(default_factory=InferConfig)
    prompt_translate: PromptTranslate = field(default_factory=PromptTranslate)
    remote_config: RemoteConfig = field(default_factory=RemoteConfig)

    @staticmethod
    def load(toml: dict[str, Any]) -> "Config":
        return Config(
            magic_points=MagicPointConfig.load(toml["magic_points"]),
            infer=InferConfig.load(toml["infer"]),
            prompt_translate=PromptTranslate.load(toml["prompt_translate"]),
            remote_config=RemoteConfig.load(toml["remote_config"]),
        )

_default_filepath = "config.toml"

@cache
def get_config(filepath: str | None = None) -> Config:
    if filepath is None:
        filepath = _default_filepath

    with open(filepath, "rb") as fp:
        toml = tomllib.load(fp)

    return Config.load(toml)


def set_config_file_path(path: str):
    global _default_filepath
    _default_filepath = path
    reload_config()


def reload_config() -> None:
    get_config.cache_clear()
