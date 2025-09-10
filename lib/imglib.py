from PIL import Image, ImageFile
from typing import AsyncIterator
import httpx
import io
from contextlib import asynccontextmanager
import numpy
import cv2
import base64


@asynccontextmanager
async def open_remote_image(url: str) -> AsyncIterator[ImageFile.ImageFile]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.content

        f = Image.open(io.BytesIO(resp.content))

        try:
            yield f
        finally:
            f.close()


def keep_ratio_stretch_to_height(src: Image.Image, h: int = 1080) -> Image.Image:
    ipt = numpy.array(src)

    wh_ratio = src.width / src.height
    w = int(h * wh_ratio)

    res = cv2.resize(ipt, (w, h), interpolation=cv2.INTER_CUBIC)

    return Image.fromarray(res)


def resize(src: Image.Image, w: int = 1920, h: int = 1080) -> Image.Image:
    new_image = Image.new("RGB", (w, h), (255, 255, 255))

    x = (w - src.width) // 2
    y = (h - src.height) // 2

    new_image.paste(src, (x, y))

    return new_image


def image_to_b64(img: Image.Image, format: str = "png") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=format)
    return base64.b64encode(buf.getvalue())
