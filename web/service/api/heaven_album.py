from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from loguru import logger
from wechat.access_token import PersistenceWxAccessToken
from wechat.storage import WxCloudStorage
from wechat.rpc import HeavenAlbum
import persistence.sysconf
from zhipuai_client import ZhipuaiClient
import io
import httpx

import secrets
from models import inferences, users

import imglib
from PIL import Image, ImageChops
import asyncio
import oss
import secrets


class APIResponse(BaseModel):
    code: int = 0
    msg: str = "ok"


class CreateHeavenAlbumTaskRequest(BaseModel):
    tid: str
    openid: str
    images: list[str]
    name: str
    gender: inferences.Gender
    faith: list[str]
    hobby: list[str]


class InferenceRequest(BaseModel):
    init_image: str | None = None
    mask_image: str | None = None
    text_prompt: str | None = None
    segment_prompt: str | None = None


class InferenceResult(BaseModel):
    rmbg_mask: str | None = None
    rmbg_rgba: str | None = None
    image: str | None = None


class InferenceResponse(BaseModel):
    code: int
    msg: str
    cost_time: str | None = None
    result: InferenceResult | None = None


class InferenceError(Exception):
    pass


async def generate_background_mask(src: Image.Image) -> Image.Image:
    url = "http://app4.zpanx.cn:8701" + "/segment_any"
    req_body = InferenceRequest(
        init_image=imglib.image_to_b64(src).decode(), segment_prompt="rmbg"
    )

    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(url, json=req_body.model_dump(exclude_none=True))
        res = InferenceResponse.model_validate_json(response.content)

        if res.code != 0:
            raise InferenceError(res.msg)
        if res.result == None or res.result.rmbg_mask == None:
            raise InferenceError("no segment result")

        mask: Image.Image | None = None
        async with imglib.open_remote_image(res.result.rmbg_mask) as raw:
            mask = ImageChops.invert(raw)

        return mask


async def generate_normalized_image(
    src: Image.Image, mask: Image.Image, prompt: str
) -> Image.Image:
    url = "http://app4.zpanx.cn:8701" + "/replace_with_any"
    req = InferenceRequest(
        init_image=imglib.image_to_b64(src).decode(),
        mask_image=imglib.image_to_b64(mask).decode(),
        text_prompt=prompt,
    )

    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post(url, json=req.model_dump(exclude_none=True))

        res = InferenceResponse.model_validate_json(response.content)

        if res.code != 0:
            raise InferenceError(res.msg)
        if res.result == None or res.result.image == None:
            raise InferenceError("no inference result")

        result: Image.Image | None = None
        async with imglib.open_remote_image(res.result.image) as img:
            result = img.copy()

        return result


async def normailize_input_image(url: str) -> Image.Image:
    res: Image.Image | None = None

    async with imglib.open_remote_image(url) as ipt:
        stretched = await asyncio.to_thread(imglib.keep_ratio_stretch_to_height, ipt)
        extended = await asyncio.to_thread(imglib.resize, stretched)
        mask = await generate_background_mask(extended)
        text_prompt = "A surreal cosmic starry sky, vast glowing nebulae, luminous galaxies, dreamy aurora-like lights, surrealism style, vibrant colors, deep blues and purples with glowing pink and teal highlights, ultra-detailed, cinematic, ethereal atmosphere"
        res = await generate_normalized_image(extended, mask, prompt=text_prompt)

    return res


router = APIRouter(prefix="/heaven_album")


class UploadResp(BaseModel):
    errcode: int
    errmsg: str
    url: str
    token: str
    authorization: str
    file_id: str
    cos_file_id: str


async def prepare_inference(
    tid: str,
    ai_conf: persistence.sysconf.ZhipuaiConfig,
) -> None:

    logger.info(f"preparing task {tid}")
    task = await inferences.HeavenAlbum.get(tid)

    if not task:
        logger.error(f"try prepare task, but no such task {tid}")
        return

    async with oss.save_file(f"{secrets.token_hex(8)}.png", "image/png") as writer:
        norimalized_input = await normailize_input_image(task.picture)
        buf = io.BytesIO()
        await asyncio.to_thread(norimalized_input.save, buf, "png")
        await writer.write_bytes(buf.getvalue())
        task.norimalized_picture = writer.file_id
        await task.save()

    ai_client = ZhipuaiClient(ai_conf.apikey)

    # generate prompt
    character = ai_conf.heaven_album.user_prompt
    character = (
        character.replace("{{gender}}", task.gender)
        .replace("{{faith}}", ", ".join(task.faith))
        .replace("{{hobby_list}}", ", ".join([f"喜欢{x}" for x in task.hobby]))
    )

    prompts = await ai_client.heaven_album_prompt(
        ai_conf.heaven_album.model,
        ai_conf.heaven_album.system_prompt,
        character,
    )

    task.ipt_sys_prompt = ai_conf.heaven_album.system_prompt
    task.ipt_user_prompt = character
    task.model = ai_conf.heaven_album.model
    task.aigc_prompts = [x for x in prompts.splitlines() if len(x) != 0]
    await task.set_ready()

    logger.info(f"task {tid} ready to infer, enqueue waiting list...")


@router.post("/task")
async def create_heaven_album_task(
    req: CreateHeavenAlbumTaskRequest, bg: BackgroundTasks
) -> APIResponse:
    zhipuai_conf = await persistence.sysconf.ZhipuaiConfig.all().first_or_none()
    if not zhipuai_conf:
        raise ValueError("no zhipuai config")

    infer_conf = await persistence.sysconf.InferenceConfig.all().first_or_none()
    if not infer_conf:
        raise ValueError("no infer config")

    logger.info("request to create new heaven album task.")
    logger.info(f"user openid {req.openid}, relevant task id {req.tid}")

    task = inferences.HeavenAlbum(
        inference_endpoint=infer_conf.service_host
        + infer_conf.endpoints.edit_with_prompt,
        nickname=req.name,
        picture=req.images[0],
        gender=req.gender,
        faith=req.faith,
        hobby=req.hobby,
        uid=users.UserID(source=users.UserSource.wx_openid, ident=req.openid),
        userdata=req.tid,
        callback=f"https://www.lingqi.tech/aigc/api/heaven_album/task/callback",
    )
    await task.save()
    logger.info(f"append inference task {str(task.id)}")

    bg.add_task(prepare_inference, str(task.id), zhipuai_conf)

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

            # FIXME this part too long.
            images = []
            for url in req.result.data:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(url)
                    path = f"result/{req.userdata}/{secrets.token_hex(3)}.jpg"
                    file_id = await cloud_storage.upload(path, io.BytesIO(resp.content))
                    logger.info(f"uploaded file id: {file_id}")
                    images.append(file_id)

            # TODO Append normalized picture as a result.

            await rpc_client.update_task(req.userdata, req.state, images)

    return APIResponse()
