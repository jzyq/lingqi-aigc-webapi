from pydantic import BaseModel


class BannerData(BaseModel):
    image: str
    video: str


class Showcase(BaseModel):
    original: str
    result: str


class Prompt(BaseModel):
    name: str
    prompt: str


class ShowcasesAndPrompts(BaseModel):
    showcase: list[Showcase]
    prompts: list[Prompt]


class Magic(BaseModel):
    partial: ShowcasesAndPrompts
    powerful: ShowcasesAndPrompts
    i2v: ShowcasesAndPrompts


class MainPageData(BaseModel):
    banner: list[BannerData]
    magic: Magic
