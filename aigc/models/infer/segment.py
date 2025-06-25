from pydantic import BaseModel


class Result(BaseModel):
    cost_time: str
    create_style_id: str
    creation_id: str
    message: str
    rmbg_mask: str
    rmbg_rgba: str
    user_id: str


class Request(BaseModel):
    init_image: str
    segment_prompt: str
    prompt: str
    return_base64: bool = False


class Response(BaseModel):
    code: int
    msg: str
    data: list[str] = []
    cost_time: str | None = None
    oss_urls: list[str] | None = None
    result: Result | None = None
