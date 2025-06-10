from pydantic import BaseModel, Field
from uuid import uuid4


class ReplaceRequest(BaseModel):
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


class ReplaceResult(BaseModel):
    image: str


class ReplaceResponse(BaseModel):
    code: int
    msg: str
    data: list[str] | None = None
    oss_urls: list[str] | None = None
    result: ReplaceResult | None = None


class i2v:

    class Request(BaseModel):
        init_image: str
        text_prompt: str

    class Response(BaseModel):
        code: int
        msg: str
        data: list[str] | None = None
