from fastapi import APIRouter
from pydantic import BaseModel
from loguru import logger
from enum import StrEnum
from wechat.access_token import PersistenceWxAccessToken
from wechat.storage import WxCloudStorage
from wechat.rpc import HeavenAlbum
import persistence.sysconf
from zhipuai_client import ZhipuaiClient
import io
import httpx

import secrets
from models import inferences, users
from beanie import PydanticObjectId


class APIResponse(BaseModel):
    code: int = 0
    msg: str = "ok"


class Gender(StrEnum):
    male = "男"
    female = "女"


class CreateHeavenAlbumTaskRequest(BaseModel):
    tid: str
    openid: str
    images: list[str]
    name: str
    gender: Gender
    faith: list[str]
    hobby: list[str]


router = APIRouter(prefix="/heaven_album")


class UploadResp(BaseModel):
    errcode: int
    errmsg: str
    url: str
    token: str
    authorization: str
    file_id: str
    cos_file_id: str


@router.post("/task")
async def create_heaven_album_task(req: CreateHeavenAlbumTaskRequest) -> APIResponse:
    zhipuai_conf = await persistence.sysconf.ZhipuaiConfig.all().first_or_none()
    if not zhipuai_conf:
        raise ValueError("no zhipuai config")

    infer_conf = await persistence.sysconf.InferenceConfig.all().first_or_none()
    if not infer_conf:
        raise ValueError("no infer config")

    # generate prompt
    character = f"姓名: {req.name}, 性别: {req.gender}, 信仰: {' '.join(req.faith)}, 爱好: {' '.join(req.hobby)}"
    ai_client = ZhipuaiClient(zhipuai_conf.apikey)
    prompts = ai_client.heaven_album_prompt(
        zhipuai_conf.heaven_album.model,
        zhipuai_conf.heaven_album.system_prompt,
        character,
    )
    logger.debug(f"{prompts}")

    # Create new task
    tid = secrets.token_hex(12)
    task = inferences.CompositeTask(
        id=PydanticObjectId(tid),
        uid=users.UserID(source=users.UserSource.wx_openid, ident=req.openid),
        userdata=req.tid,
        callback=f"https://www.lingqi.tech/aigc/api/heaven_album/task/callback",
        requests=[
            inferences.Request.in_place(
                infer_conf.service_host + infer_conf.endpoints.edit_with_prompt,
                {"init_image": req.images[0], "text_prompt": prompts},
            )
            for _ in range(1)
        ],
    )
    await task.insert()

    return APIResponse()


@router.post("/task/callback")
async def task_down_callback(req: inferences.CallbackData) -> APIResponse:
    wx_conf = await persistence.sysconf.WechatConfig.all().first_or_none()
    if not wx_conf:
        raise ValueError("no wechat config")

    access_token = PersistenceWxAccessToken(wx_conf.appid, wx_conf.secret)
    cloud_storage = WxCloudStorage(access_token, wx_conf.cloud_env)
    rpc_client = HeavenAlbum(access_token, wx_conf.cloud_env)

    match req.state:
        case inferences.State.error:
            await rpc_client.update_task(req.userdata, req.state)
        case inferences.State.cancel:
            await rpc_client.update_task(req.userdata, req.state)
        case inferences.State.down:
            if not req.result:
                raise ValueError("task down must have result")
            if not isinstance(req.result, inferences.CompositeResponse):
                raise TypeError("result must be a composite response")

            images = []
            for url in req.result.data:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url)
                    path = f"result/{req.userdata}/{secrets.token_hex(3)}.jpg"
                    file_id = await cloud_storage.upload(path, io.BytesIO(resp.content))
                    logger.info(f"uploaded file id: {file_id}")
                    images.append(file_id)
            await rpc_client.update_task(req.userdata, req.state, images)

    return APIResponse()
