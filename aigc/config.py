import tomllib
from functools import cache
from dataclasses import dataclass, field
from typing import Any

_config_file: str = "config.template.toml"


@cache
def _c() -> dict[str, Any]:
    with open(_config_file, "rb") as fp:
        return tomllib.load(fp)


def setup_config_file(path: str):
    global _config_file
    _config_file = path
    reload_config()


def reload_config() -> None:
    _c.cache_clear()


@dataclass
class WebConfig:
    host: str = field(default_factory=lambda: _c()["web"]["host"])
    port: int = field(default_factory=lambda: int(_c()["web"]["port"]))
    session_ttl: int = field(default_factory=lambda: int(_c()["web"]["session_ttl"]))


@dataclass
class RedisConfig:
    host: str = field(default_factory=lambda: _c()["redis"]["host"])
    port: int = field(default_factory=lambda: int(_c()["redis"]["port"]))
    db: int = field(default_factory=lambda: int(_c()["redis"]["db"]))


@dataclass
class DatabaseConfig:
    file: str = field(default_factory=lambda: _c()["database"]["file"])


def _read_secrets(key: str) -> str:
    return _c()["wechat"]["secrets"][key]


@dataclass
class WechatSecretConfig:
    login_id: str = field(default_factory=lambda: _read_secrets("login_id"))
    app_id: str = field(default_factory=lambda: _read_secrets("app_id"))
    app_secret: str = field(default_factory=lambda: _read_secrets("app_secret"))
    mch_id: str = field(default_factory=lambda: _read_secrets("mch_id"))
    mch_cert_serial: str = field(
        default_factory=lambda: _read_secrets("mch_cert_serial")
    )
    pub_key_id: str = field(default_factory=lambda: _read_secrets("pub_key_id"))
    api_v3_pwd: str = field(default_factory=lambda: _read_secrets("api_v3_pwd"))
    api_client_key_path: str = field(
        default_factory=lambda: _read_secrets("api_client_key_path")
    )
    pub_key_path: str = field(default_factory=lambda: _read_secrets("pub_key_path"))


@dataclass
class WechatConfig:
    secrets: WechatSecretConfig = field(default_factory=WechatSecretConfig)
    login_redirect: str = field(
        default_factory=lambda: _c()["wechat"]["logint_redirect"]
    )
    payment_callback: str = field(
        default_factory=lambda: _c()["wechat"]["payment_callback"]
    )
    payment_expires: int = field(
        default_factory=lambda: int(_c()["wechat"]["payment_expires"])
    )


@dataclass
class MagicPointSubscription:
    price: int
    month: int
    points: int


def _load_magic_point_subscription() -> list[MagicPointSubscription]:
    res: list[MagicPointSubscription] = []
    for item in _c()["magic_points"]["subscriptions"]:
        s = MagicPointSubscription(
            price=int(item["price"]),
            month=int(item["month"]),
            points=int(item["points"]),
        )
        res.append(s)
    return res


@dataclass
class MagicPointConfig:
    trail_free_point: int = field(
        default_factory=lambda: int(_c()["magic_points"]["trail_free_point"])
    )
    subscriptions: list[MagicPointSubscription] = field(
        default_factory=_load_magic_point_subscription
    )


@dataclass
class InferConfig:
    base: str = field(default_factory=lambda: _c()["infer"]["base"])
    long_poll_timeout: int = field(
        default_factory=lambda: _c()["infer"]["long_poll_timeout"]
    )

    replace_any: str = field(default_factory=lambda: _c()["infer"]["replace_any"])
    replace_reference: str = field(
        default_factory=lambda: _c()["infer"]["replace_reference"]
    )
    segment_any: str = field(default_factory=lambda: _c()["infer"]["segment_any"])
    image_to_video: str = field(default_factory=lambda: _c()["infer"]["image_to_video"])


# Just read this config when needed.
@dataclass
class Config:
    web: WebConfig = field(default_factory=WebConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    wechat: WechatConfig = field(default_factory=WechatConfig)
    magic_points: MagicPointConfig = field(default_factory=MagicPointConfig)
    infer: InferConfig = field(default_factory=InferConfig)
