import httpx
from ..models.infer.segment import Request, Response
from loguru import logger
from pydantic import ValidationError


async def segment(url: str, req: Request) -> Response:
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.post(url, json=req.model_dump())
        try:
            result = Response.model_validate(
                resp.raise_for_status().json()
            )
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"infer srv error, {e.response.reason_phrase}")
            return Response(
                code=e.response.status_code, msg=e.response.reason_phrase
            )
        except ValidationError as e:
            logger.error(f"parse response error, {repr(e)}")
            return Response(code=400, msg=repr(e))
