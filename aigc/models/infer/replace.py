from pydantic import BaseModel, Field
from uuid import uuid4


class Request(BaseModel):
    init_image: str | None = None
    mask_image: str | None = None
    reference_image: str | None = None
    reference_mask_image: str | None = None
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    creation_id: str = Field(default_factory=lambda: str(uuid4()))
    create_style_id: str = Field(default_factory=lambda: str(uuid4()))
    is_callback: bool = False
    callback_url: str | None = None
    return_base64: bool = True
    num_frames: int = 2
    num_steps: int = 2
    text_prompt: str = ""


class Result(BaseModel):
    image: str


class Response(BaseModel):
    code: int
    msg: str
    data: list[str] | None = None
    oss_urls: list[str] | None = None
    result: Result | None = None
