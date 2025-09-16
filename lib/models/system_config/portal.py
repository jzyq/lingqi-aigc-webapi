from .base import SystemConfig
from pydantic import BaseModel
from typing import Any


class BannerItem(BaseModel):
    image: str
    video: str


class ShowcaseItem(BaseModel):
    original: str
    result: str


class PromptItem(BaseModel):
    name: str
    prompt: str


class MagicItem(BaseModel):
    showcase: list[ShowcaseItem]
    prompts: list[PromptItem]


class Magic(BaseModel):
    partial: MagicItem
    powerful: MagicItem
    i2v: MagicItem


class ShortcutItem(BaseModel):
    type: str
    magic: str
    teach: str
    params: Any


class PortalConfig(SystemConfig):
    banners: list[BannerItem] | None = None
    magic: Magic | None = None
    shortcuts: list[ShortcutItem] | None = None
