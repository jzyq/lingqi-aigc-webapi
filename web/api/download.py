from fastapi import APIRouter, Response, Depends
from fastapi.responses import StreamingResponse
import minio  # type: ignore
from urllib3 import BaseHTTPResponse
import deps
import io

router = APIRouter(prefix="/download")


@router.get("/{bucket_name}/{object_name}")
async def download_resource(
    bucket_name: str, object_name: str, mc: minio.Minio = Depends(deps.get_minio_client)
) -> Response:

    if not mc.bucket_exists(bucket_name):
        return Response(status_code=404)

    resp: BaseHTTPResponse | None = None
    try:
        resp = mc.get_object(bucket_name, object_name)
        return StreamingResponse(
            content=io.BytesIO(resp.data),
            headers={
                "content-length": resp.headers["content-length"],
                "content-type": resp.headers["content-type"],
            },
        )
    finally:
        if resp:
            resp.close()
            resp.release_conn()
