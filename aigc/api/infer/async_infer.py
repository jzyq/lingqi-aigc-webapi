from fastapi import APIRouter, Depends, Response, Request
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from functools import cache
from typing import Annotated, Any, Callable, Coroutine

from ... import background_inference as bgi
from ... import common
from ... import deps
from pydantic import BaseModel


# Exception raise when try get response no wait but request still in progress.
class NotDownError(Exception):

    def __init__(self, tid: str) -> None:
        self.tid: str = tid

    def __str__(self) -> str:
        return f"request {self.tid} still in progress."


# Custom route class in order to handle exceptions.
class AsyncInferRoute(APIRoute):

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        origional_handler = super().get_route_handler()

        async def custom_handler(req: Request) -> Response:
            try:
                return await origional_handler(req)

            except NotDownError as exc:
                return JSONResponse(content={"code": 10, "msg": str(exc)})

            except common.excpetions.NotFoundError:
                return JSONResponse(
                    content={"code": 10, "msg": "no such request, check tid."}
                )

        return custom_handler


# Get background request dict with cache
# It always call with no arguments so it always return the same object.
# Like a singleton.
@cache
def get_background_request_dict() -> bgi.ReqDict:
    return bgi.ReqDict()


# Depend use to manage background requests.
BackgroundRequests = Annotated[bgi.ReqDict, Depends(get_background_request_dict)]


# Response model when append new request and query requests state.
class RequestState(BaseModel):
    tid: str
    state: bgi.State


# Define router
router = APIRouter(prefix="/async/infer", route_class=AsyncInferRoute)


# API to query background requests current state, no block.
@router.get("/{tid}/state")
async def get_req_state(
    tid: str, ses: deps.UserSession, requests: BackgroundRequests
) -> RequestState:
    state = await requests.state(tid)
    return RequestState(tid=tid, state=state)


# API to get result of a request if have, no block.
@router.get("/{tid}/result")
async def get_req_result(
    tid: str, ses: deps.UserSession, requests: BackgroundRequests
) -> Response:
    res = await requests.response(tid)
    if res is None:
        raise NotDownError(tid)
    return Response(content=res.content, headers=res.headers)
