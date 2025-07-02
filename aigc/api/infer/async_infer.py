from fastapi import APIRouter, Depends, Response, Request, BackgroundTasks
from functools import cache
from typing import Annotated, Mapping

from ... import deps
from pydantic import BaseModel
import httpx
from .common import point_manager, NoPointError, InferResponse, InferRoute, NotDownError
import asyncio
from dataclasses import dataclass, field
import secrets
from loguru import logger

STATE_IN_PROGRESS: str = "in progress"
STATE_DOWN: str = "down"


# Response model when append new request and query requests state.
class GetStateResponse(BaseModel):
    code: int
    msg: str
    tid: str
    state: str


# Response model when create new background task.
class CreateRequestResponse(BaseModel):
    code: int
    msg: str
    tid: str


# Define background request metadata.
@dataclass
class BackgroundRequest:
    uid: int
    point: int
    content: bytes
    headers: Mapping[str, str]
    tid: str = field(default_factory=lambda: secrets.token_hex(8))
    exception: Exception | None = field(default=None, init=False)
    response: Response | None = field(default=None, init=False)
    cond: asyncio.Condition = field(default_factory=asyncio.Condition, init=False)


# Class use to manage background requests.
class BackgroundRequestsDict:

    def __init__(self) -> None:
        self.lock = asyncio.Lock()
        self.responses_by_uid: dict[int, dict[str, BackgroundRequest]] = {}


# A function to build requests dict with cache.
# Due to the arguments always the same so it always return same object.
@cache
def get_requests_dict() -> BackgroundRequestsDict:
    return BackgroundRequestsDict()


# Depends of requests dict.
RequestsDict = Annotated[BackgroundRequestsDict, Depends(get_requests_dict)]


# Forward request to infer server, and set raw response when complete.
async def forward_to_infer(
    url: str,
    req: BackgroundRequest,
    db: deps.Database,
):
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.post(url, content=req.content, headers=req.headers)
        logger.debug(f"infer server response request {req.tid}")

    try:
        resp = resp.raise_for_status()

        infer_response = InferResponse.model_validate_json(resp.content)

        # If infer have error, recharge point.
        if infer_response.code != 0:
            async with point_manager(req.uid, db) as pm:
                pm.recharge(req.point)
                logger.info(f"background infer {req.tid} error, recharge point.")

        logger.info(f"background infer request {req.tid} complete.")

        response = Response(content=resp.content, headers=resp.headers)
        async with req.cond:
            req.response = response
            req.cond.notify_all()

    except Exception as exc:
        async with req.cond:
            req.exception = exc
            req.cond.notify_all()

        # If have exception, recharge point as well.
        async with point_manager(req.uid, db) as pm:
            pm.recharge(req.point)
            logger.warning(
                f"recharge point due to exception raise from background request {req.tid}"
            )


# Define router
router = APIRouter(prefix="/async/infer", route_class=InferRoute)


# API to query background requests current state, no block.
@router.get("/{tid}/state")
async def get_req_state(
    tid: str, ses: deps.UserSession, req_dict: RequestsDict
) -> GetStateResponse:

    response = GetStateResponse(code=0, msg="ok", tid=tid, state=STATE_IN_PROGRESS)

    async with req_dict.lock:
        infer_request = req_dict.responses_by_uid[ses.uid][tid]
        if infer_request.exception or infer_request.response:
            response.state = STATE_DOWN

    return response


# API to get result of a request if have, no block.
@router.get("/{tid}/result")
async def get_req_result(
    tid: str, ses: deps.UserSession, req_dict: RequestsDict
) -> Response:

    async with req_dict.lock:
        infer_request = req_dict.responses_by_uid[ses.uid][tid]

        if infer_request.exception:
            raise infer_request.exception

        if infer_request.response:
            return infer_request.response

        raise NotDownError(tid)


# API to create a background replace with any infer request.
@router.post("/replace_any")
async def replace_with_any(
    req: Request,
    ses: deps.UserSession,
    db: deps.Database,
    conf: deps.Config,
    req_dict: RequestsDict,
    bg: BackgroundTasks,
) -> CreateRequestResponse:
    async with point_manager(ses.uid, db) as pm:
        if pm.magic_points < 10:
            raise NoPointError(ses.uid)

    # Gen task id, create memories.
    content = await req.body()
    headers = req.headers
    bg_req = BackgroundRequest(ses.uid, 10, content, headers)

    async with req_dict.lock:
        if ses.uid not in req_dict.responses_by_uid:
            req_dict.responses_by_uid[ses.uid] = {}
        req_dict.responses_by_uid[ses.uid][bg_req.tid] = bg_req

    # Add background task.
    url = conf.infer.base + conf.infer.replace_any
    bg.add_task(forward_to_infer, url, bg_req, db)

    # Pre deduct point prevent excceed limit.
    pm.deduct(10)
    return CreateRequestResponse(code=0, msg="ok", tid=bg_req.tid)


# API to create a background replace with reference infer request.
@router.post("/replace_with_reference")
async def replace_with_reference(
    req: Request,
    ses: deps.UserSession,
    db: deps.Database,
    conf: deps.Config,
    req_dict: RequestsDict,
    bg: BackgroundTasks,
) -> CreateRequestResponse:
    async with point_manager(ses.uid, db) as pm:
        if pm.magic_points < 10:
            raise NoPointError(ses.uid)

    # Gen task id, create memories.
    content = await req.body()
    headers = req.headers
    bg_req = BackgroundRequest(ses.uid, 10, content, headers)

    async with req_dict.lock:
        if ses.uid not in req_dict.responses_by_uid:
            req_dict.responses_by_uid[ses.uid] = {}
        req_dict.responses_by_uid[ses.uid][bg_req.tid] = bg_req

    # Add background task.
    url = conf.infer.base + conf.infer.replace_reference
    bg.add_task(forward_to_infer, url, bg_req, db)

    # Pre deduct point prevent excceed limit.
    pm.deduct(10)
    return CreateRequestResponse(code=0, msg="ok", tid=bg_req.tid)


# API to create a background image to video request.
@router.post("/image_to_video")
async def image_to_video(
    req: Request,
    ses: deps.UserSession,
    db: deps.Database,
    conf: deps.Config,
    req_dict: RequestsDict,
    bg: BackgroundTasks,
) -> CreateRequestResponse:
    async with point_manager(ses.uid, db) as pm:
        if pm.magic_points < 10:
            raise NoPointError(ses.uid)

    # Gen task id, create memories.
    content = await req.body()
    headers = req.headers
    bg_req = BackgroundRequest(ses.uid, 10, content, headers)

    async with req_dict.lock:
        if ses.uid not in req_dict.responses_by_uid:
            req_dict.responses_by_uid[ses.uid] = {}
        req_dict.responses_by_uid[ses.uid][bg_req.tid] = bg_req

    # Add background task.
    url = conf.infer.base + conf.infer.image_to_video
    bg.add_task(forward_to_infer, url, bg_req, db)

    # Pre deduct point prevent excceed limit.
    pm.deduct(10)
    return CreateRequestResponse(code=0, msg="ok", tid=bg_req.tid)


# API to create a background segment any infer request.
@router.post("/segment_any")
async def segment_any(
    req: Request,
    ses: deps.UserSession,
    db: deps.Database,
    conf: deps.Config,
    req_dict: RequestsDict,
    bg: BackgroundTasks,
) -> CreateRequestResponse:
    async with point_manager(ses.uid, db) as pm:
        if pm.magic_points < 10:
            raise NoPointError(ses.uid)

    # Gen task id, create memories.
    content = await req.body()
    headers = req.headers
    bg_req = BackgroundRequest(ses.uid, 10, content, headers)

    async with req_dict.lock:
        if ses.uid not in req_dict.responses_by_uid:
            req_dict.responses_by_uid[ses.uid] = {}
        req_dict.responses_by_uid[ses.uid][bg_req.tid] = bg_req

    # Add background task.
    url = conf.infer.base + conf.infer.segment_any
    bg.add_task(forward_to_infer, url, bg_req, db)

    # Pre deduct point prevent excceed limit.
    pm.deduct(10)
    return CreateRequestResponse(code=0, msg="ok", tid=bg_req.tid)
