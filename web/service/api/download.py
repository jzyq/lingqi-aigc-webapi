from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
import oss

router = APIRouter(prefix="/download")


@router.get("/{file_id}")
async def download_resource(file_id: str) -> Response:
    async with oss.load_file(file_id) as reader:
        return StreamingResponse(
            content=reader,
            headers={
                "content-length": str(reader.length),
                "content-type": reader.content_type,
            },
        )
