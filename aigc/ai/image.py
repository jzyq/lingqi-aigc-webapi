import httpx
from ..models.infer.replace import Request, Response
from loguru import logger


async def replace_with_any(url: str, req: Request) -> Response:
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.post(url, json=req.model_dump(by_alias=True))

    if resp.status_code != 200:
        logger.error(
            f"infer server response status code {resp.status_code}, detail: {resp.text}"
        )
        return Response(code=2, msg="infer server unavailable.")

    if resp.headers["content-type"] != "application/json":
        logger.error(
            f"expect infer result to be a json but actual is {resp.headers['content-type']}"
        )
        logger.error(f"resp: {resp.text}")
        return Response(code=3, msg="response data not json")

    logger.debug("infer complete.")
    return Response.model_validate_json(resp.content)
