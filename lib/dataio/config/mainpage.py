from pydantic import BaseModel
from typing import Sequence, Any
from models.system_config import portal
from .. import errors


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
    showcase: Sequence[ShowcaseItem]
    prompts: Sequence[PromptItem]


class ShortcutItem(BaseModel):
    type: str
    magic: str
    teach: str
    params: Any


def _magic_item_to_model(item: MagicItem) -> portal.MagicItem:
    showcases: list[portal.ShowcaseItem] = []
    for s in item.showcase:
        showcases.append(portal.ShowcaseItem(original=s.original, result=s.result))

    prompts: list[portal.PromptItem] = []
    for p in item.prompts:
        prompts.append(portal.PromptItem(name=p.name, prompt=p.prompt))

    res = portal.MagicItem(showcase=showcases, prompts=prompts)
    return res


def _model_to_magic_item(model: portal.MagicItem) -> MagicItem:
    showcases: list[ShowcaseItem] = []
    for s in model.showcase:
        showcases.append(ShowcaseItem(original=s.original, result=s.result))

    prompts: list[PromptItem] = []
    for p in model.prompts:
        prompts.append(PromptItem(name=p.name, prompt=p.prompt))

    res = MagicItem(showcase=showcases, prompts=prompts)
    return res


class Magic(BaseModel):
    partial: MagicItem
    powerful: MagicItem
    i2v: MagicItem

    @staticmethod
    async def get() -> "Magic":
        conf = await portal.PortalConfig.find_one()
        if not conf or not conf.magic:
            raise errors.NotExists("portal magic config not exists")

        magic = Magic(
            partial=_model_to_magic_item(conf.magic.partial),
            powerful=_model_to_magic_item(conf.magic.powerful),
            i2v=_model_to_magic_item(conf.magic.i2v),
        )
        return magic

    async def save(self) -> None:
        conf = await portal.PortalConfig.find_one()
        if not conf:
            conf = portal.PortalConfig()

        magic = portal.Magic(
            partial=_magic_item_to_model(self.partial),
            powerful=_magic_item_to_model(self.powerful),
            i2v=_magic_item_to_model(self.i2v),
        )
        conf.magic = magic
        await conf.save()


class Banner(BaseModel):
    banners: Sequence[BannerItem]

    @staticmethod
    async def get() -> "Banner":
        conf = await portal.PortalConfig.find_one()
        if not conf or not conf.banners:
            raise errors.NotExists("portal banner config not exists")

        banners: list[BannerItem] = []
        for b in conf.banners:
            banners.append(BannerItem(image=b.image, video=b.video))
        return Banner(banners=banners)

    async def save(self) -> None:
        conf = await portal.PortalConfig.find_one()
        if not conf:
            conf = portal.PortalConfig()

        banners: list[portal.BannerItem] = []
        for b in self.banners:
            banners.append(portal.BannerItem(image=b.image, video=b.video))

        conf.banners = banners
        await conf.save()


class Shortcut(BaseModel):
    shortcuts: Sequence[ShortcutItem]

    @staticmethod
    async def get() -> "Shortcut":
        conf = await portal.PortalConfig.find_one()
        if not conf or not conf.shortcuts:
            raise errors.NotExists("portal shortcut config not exists")

        shortcuts: list[ShortcutItem] = []
        for s in conf.shortcuts:
            shortcuts.append(
                ShortcutItem(type=s.type, magic=s.magic, teach=s.teach, params=s.params)
            )
        return Shortcut(shortcuts=shortcuts)

    async def save(self) -> None:
        conf = await portal.PortalConfig.find_one()
        if not conf:
            conf = portal.PortalConfig()

        shortcuts: list[portal.ShortcutItem] = []
        for s in self.shortcuts:
            shortcuts.append(
                portal.ShortcutItem(
                    type=s.type, magic=s.magic, teach=s.teach, params=s.params
                )
            )

        conf.shortcuts = shortcuts
        await conf.save()
