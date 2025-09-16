from fastapi import APIRouter
from pydantic import BaseModel
from dataio.config import mainpage


class APIResponse(BaseModel):
    code: int = 0
    msg: str = "ok"


class BannerItemList(APIResponse):
    items: list[mainpage.BannerItem]


class MagicShowcases(APIResponse):
    magic: mainpage.Magic


class ShortcutRespnose(APIResponse):
    shortcuts: list[mainpage.ShortcutItem] = []


router = APIRouter(prefix="/main")


@router.get("/banner")
async def get_main_page_banner_data() -> BannerItemList:
    banner = await mainpage.Banner.get()
    res = BannerItemList(items=[])
    for i in banner.banners:
        res.items.append(i)
    return res


@router.get("/shortcut")
async def get_shortcuts_data() -> ShortcutRespnose:
    shortcut = await mainpage.Shortcut.get()
    resp = ShortcutRespnose(shortcuts=[])
    for s in shortcut.shortcuts:
        resp.shortcuts.append(s)
    return resp


@router.get("/magic")
async def get_main_page_showcase_data() -> MagicShowcases:
    magic = await mainpage.Magic.get()
    resp = MagicShowcases(magic=magic)
    return resp
