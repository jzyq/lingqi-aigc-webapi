from fastapi import APIRouter, Response
from fastapi.responses import FileResponse
import os

router = APIRouter(prefix="/download")


@router.get("/{filepath}")
async def download_resource(filepath: str) -> Response:
    actual_path = "static/" + filepath

    if os.path.exists(actual_path):
        return FileResponse("static/" + filepath)
    else:
        return Response(status_code=404)
