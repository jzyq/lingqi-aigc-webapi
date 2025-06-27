import asyncio
import secrets

from pydantic import BaseModel, Field

from .err import *
import httpx

# The length represent how many bytes when generate token
# Covert to hex str will double the length.
CREATION_TOKEN_LEN = 8


class GenReq(BaseModel):
    image_url: str = Field(serialization_alias="init_image")
    prompt:  str = Field(serialization_alias="text_prompt")
    user_id: str
    creation_id: str = Field(
        default_factory=lambda: secrets.token_hex(CREATION_TOKEN_LEN))


class Result(BaseModel):
    cost_time: str
    create_style_id: str
    creation_id: str
    data: str
    message: str
    text_prompt: str
    user_id: str
    video: str
    video_image: str


class GenResp(BaseModel):
    code: int
    msg: str
    cost_time: str
    data: list[str]
    result: Result


async def generate(url: str, uid: int, image_url: str, prompt: str, timeout_s: int) -> GenResp:
    req = GenReq(image_url=image_url, prompt=prompt, user_id=str(uid))
    json_data = req.model_dump(by_alias=True, exclude_none=True)
    async with httpx.AsyncClient() as client:
        task = client.post(url=url, json=json_data)

    try:
        resp = await asyncio.wait_for(task, timeout=timeout_s)
        if resp.status_code != 200:
            raise ServerError("infer server unavilable.")

        body = resp.json()
        if "error" in body:
            raise GenerateError(body["error"])

        resp = GenResp.model_validate(body)
        return resp

    except TimeoutError:
        raise GenerateError("generate timeout.")


@staticmethod
async def async_generate(image_url: str, prompt: str, callback_url: str) -> None:
    pass
