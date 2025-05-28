from pydantic import BaseModel, Field
import uuid
import requests

BASE_URL = "http://zdxai.iepose.cn"
TRYON_CLOTHE_URL = BASE_URL + "/replace_clothes_with_reference"
REPLACE_WITH_PROMPT_URL = BASE_URL + "/replace_with_prompt"
REPLACE_WITH_REFERENCE_URL = BASE_URL + "/replace_with_reference"


def uuid4() -> str:
    return str(uuid.uuid4())


class Request(BaseModel):
    init_image: str
    mask_image: str
    reference_image: str | None = Field(
        default=None, serialization_alias="userdefined")
    tops: bool = False
    bottoms: bool = False
    whole: bool = False
    user_id: str = Field(default_factory=uuid4)
    creation_id: str = Field(default_factory=uuid4)
    create_style_id: str = Field(default_factory=uuid4)
    is_callback: bool = False
    text_prompt: str = ""


class ResponseData(BaseModel):
    image: str
    oss_url: list[str]


class Response(BaseModel):
    code: int
    msg: str
    data: ResponseData


def replace_with_reference(input_image_b64: str, mask_b64: str, reference_image_b64: str | None = None, prompt: str = "") -> Response:
    request = Request(init_image=input_image_b64, mask_image=mask_b64,
                      reference_image=reference_image_b64, text_prompt=prompt)
    resp = requests.post(REPLACE_WITH_REFERENCE_URL,
                         json=request.model_dump(by_alias=True))
    if resp.status_code == 200:
        return Response.model_validate_json(resp.content)
    raise Exception(resp.content.decode())



def replace_with_prompt(input_image_b64: str, mask_b64: str, prompt: str) -> Response:
    request = Request(init_image=input_image_b64, mask_image=mask_b64, text_prompt=prompt)
    resp = requests.post(REPLACE_WITH_PROMPT_URL,
                         json=request.model_dump(by_alias=True))
    if resp.status_code == 200:
        return Response.model_validate_json(resp.content)
    raise Exception(resp.content.decode())