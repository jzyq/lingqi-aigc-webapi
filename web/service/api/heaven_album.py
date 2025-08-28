from fastapi import APIRouter, Request
from pydantic import BaseModel
from loguru import logger
from enum import StrEnum
from wechat.access_token import PersistenceWxAccessToken
from wechat.storage import WxCloudStorage
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
        tid=req.tid,
        callback=f"https://www.lingqi.tech/aigc/api/heaven_album/task/{tid}/callback",
        requests=[
            inferences.Request.in_place(
                infer_conf.service_host + infer_conf.endpoints.edit_with_prompt,
                {"init_image": req.images[0], "text_prompt": prompts},
            )
            for _ in range(5)
        ],
    )
    await task.insert()

    return APIResponse()


@router.post("/task/{tid}/callback")
async def task_down_callback(tid: str, req: Request) -> APIResponse:
    wx_conf = await persistence.sysconf.WechatConfig.all().first_or_none()
    if not wx_conf:
        raise ValueError("no wechat config")

    logger.info(tid)
    data = await req.json()
    logger.info(data)

    task = await inferences.CompositeTask.get(tid)
    if not task:
        logger.warning("no such task")
        return APIResponse()

    access_token = PersistenceWxAccessToken(wx_conf.appid, wx_conf.secret)
    cloud_storage = WxCloudStorage(access_token, wx_conf.cloud_env)

    images = []
    for res in data["results"]:
        url = res["result"]["image"]
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)

            path = f"result/{task.tid}/{secrets.token_hex(3)}.jpg"
            file_id = await cloud_storage.upload(path, io.BytesIO(resp.content))
            logger.info(f"uploaded file id: {file_id}")
            images.append(file_id)

    notify_url = f"https://api.weixin.qq.com/tcb/invokecloudfunction"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url=notify_url,
            params={
                "access_token": await access_token.token,
                "env": wx_conf.cloud_env,
                "name": "aigc",
            },
            json={
                "func": "heaven_album:task_down",
                "params": {"tid": task.tid, "images": images},
            },
        )
        logger.info(resp.text)

    return APIResponse()
