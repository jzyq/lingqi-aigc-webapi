from fastapi import APIRouter, Depends
from pydantic import BaseModel
from .. import models, deps


class APIResponse(BaseModel):
    code: int = 0
    msg: str = "ok"


class BannerItemList(APIResponse):
    items: list[models.mainpage.BannerData]


class MagicShowcases(APIResponse):
    magic: models.mainpage.Magic


router = APIRouter(prefix="/main")


@router.get("/banner")
async def get_main_page_banner_data(
    mainpage: models.mainpage.MainPageData = Depends(deps.get_main_page_data),
) -> BannerItemList:
    return BannerItemList(items=mainpage.banner)


@router.get("/magic")
async def get_main_page_showcase_data(
    mainpage: models.mainpage.MainPageData = Depends(deps.get_main_page_data),
) -> MagicShowcases:
    return MagicShowcases(magic=mainpage.magic)
