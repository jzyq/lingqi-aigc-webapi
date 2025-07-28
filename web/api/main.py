from fastapi import APIRouter, Depends
from pydantic import BaseModel, TypeAdapter
import redis.asyncio
import models, deps
from mainpage_config import BannerItem


class APIResponse(BaseModel):
    code: int = 0
    msg: str = "ok"


class BannerItemList(APIResponse):
    items: list[models.mainpage.BannerData]


class MagicShowcases(APIResponse):
    magic: models.mainpage.Magic


class ShortcutRespnose(APIResponse):
    shortcuts: list[models.mainpage.Shortcut] = []


router = APIRouter(prefix="/main")


@router.get("/banner")
async def get_main_page_banner_data(
    rdb: redis.asyncio.Redis = Depends(deps.get_rdb),
) -> BannerItemList:
    data = await rdb.get("aigc:banner")
    adapter = TypeAdapter(list[BannerItem])
    items = adapter.validate_json(data)

    res = BannerItemList(items=[])
    for i in items:
        d = models.mainpage.BannerData(image=i.image, video=i.video)
        res.items.append(d)

    return res


@router.get("/shortcut")
async def get_shortcuts_data(rdb: redis.asyncio.Redis = Depends(deps.get_rdb)) -> ShortcutRespnose:
    adapter = TypeAdapter(list[models.mainpage.Shortcut])
    data = await rdb.get("aigc:shortcut")
    items = adapter.validate_json(data)
    return ShortcutRespnose(shortcuts=items)


@router.get("/magic")
async def get_main_page_showcase_data(
    rdb: redis.asyncio.Redis = Depends(deps.get_rdb),
) -> MagicShowcases:
    data = await rdb.get("aigc:magic")
    magic = models.mainpage.Magic.model_validate_json(data)
    resp = MagicShowcases(magic=magic)
    return resp
