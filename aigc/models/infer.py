from pydantic import BaseModel, Field
from uuid import uuid4


class ReplaceRequest(BaseModel):
    init_image: str
    mask_image: str
    reference_image: str | None = Field(
        default=None, serialization_alias="userdefined")
    tops: bool = False
    bottoms: bool = False
    whole: bool = False
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    creation_id: str = Field(default_factory=lambda: str(uuid4()))
    create_style_id: str = Field(default_factory=lambda: str(uuid4()))
    is_callback: bool = False
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
