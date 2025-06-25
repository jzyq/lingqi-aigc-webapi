from pydantic import BaseModel


class Request(BaseModel):
    init_image: str
    text_prompt: str


class Response(BaseModel):
    code: int
    msg: str
    data: list[str] | None = None
