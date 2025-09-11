from fastapi import APIRouter, UploadFile
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response
from loguru import logger
from pydantic import BaseModel
from typing import Any, Callable, Coroutine
import oss
import gridfs.errors
import bson.errors


class APIResponse(BaseModel):
    code: int = 0
    msg: str = "ok"


class PostResponse(APIResponse):
    fid: str


class RouteHandler(APIRoute):

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original_route_handler = super().get_route_handler()

        async def route_handler(req: Request) -> Response:
            try:
                resp = await original_route_handler(req)
                return resp

            except bson.errors.InvalidId:
                resp = APIResponse(code=1, msg="invalid file id")
                return JSONResponse(content=resp.model_dump())

            except gridfs.errors.NoFile:
                resp = APIResponse(code=2, msg="no such file")
                return JSONResponse(content=resp.model_dump())

        return route_handler


router = APIRouter(route_class=RouteHandler)


@router.get("/file/{fid}")
async def get_file(fid: str) -> StreamingResponse:
    async with oss.load_file(fid) as fp:
        return StreamingResponse(
            fp,
            headers={"content-length": str(fp.length), "content-type": fp.content_type},
        )


@router.post("/file")
async def post_file(file: UploadFile) -> PostResponse:
    filename = file.filename if file.filename else ""
    content_type = file.content_type if file.content_type else ""

    async with oss.save_file(filename, content_type) as fp:
        await fp.write(file.file)
        logger.info(
            f"upload file {filename}, type: {content_type}, file id {fp.file_id}"
        )
        return PostResponse(fid=fp.file_id)
