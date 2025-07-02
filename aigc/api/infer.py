from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Callable, Coroutine

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from loguru import logger
from pydantic import BaseModel, ValidationError
from sqlmodel import Session, select

from .. import deps
from ..models.db import MagicPointSubscription, SubscriptionType


class InferRoute(APIRoute):

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original_route_handler = super().get_route_handler()

        async def route_handler(req: Request) -> Response:
            try:
                return await original_route_handler(req)

            # HTTPStatusError will raise when forward to infer srver.
            except httpx.HTTPStatusError as exc:
                logger.error(f"infer server unavailable, {repr(exc)}")
                return JSONResponse(
                    content={"code": 1, "msg": "infer server unavailable"}
                )

            # ValidationError will raise when try parse infer server response body to a json.
            except ValidationError as exc:
                logger.error(f"infer response invalid, {repr(exc)}")
                return JSONResponse(
                    content={"code": 2, "msg": "infer response invalid"}
                )

            # NoPointError will raise when user do not have enough point but try infer some.
            except NoPointError as exc:
                logger.info(f"user {exc.uid} do not have magic point")
                return JSONResponse(
                    content={"code": 3, "msg": "magic point not enough"}
                )

        return route_handler


router = APIRouter(prefix="/infer", route_class=InferRoute)


class NoPointError(Exception):
    def __init__(self, uid: int) -> None:
        self.uid = uid


class InferResponse(BaseModel):
    code: int


@asynccontextmanager
async def query_valid_subscription(
    uid: int, db: Session
) -> AsyncIterator[MagicPointSubscription]:
    query = (
        select(MagicPointSubscription)
        .where(MagicPointSubscription.uid == uid)
        .where(MagicPointSubscription.expired == False)
    )
    subscriptions = db.exec(query).all()

    trail: list[MagicPointSubscription] = []
    payed: list[MagicPointSubscription] = []

    for s in subscriptions:
        if s.stype == SubscriptionType.trail:
            trail.append(s)
        if s.stype == SubscriptionType.subscription:
            payed.append(s)

    subscription: MagicPointSubscription | None = None
    if len(payed) != 0:
        subscription = payed[0]
    elif len(trail) != 0:
        subscription = trail[0]
    else:
        raise AssertionError("no valid subscriptions")

    if subscription.remains <= 0:
        raise NoPointError(uid)

    try:
        yield subscription
    finally:
        db.commit()


async def forward_to_infer_srv(url: str, req: Request) -> tuple[int, Response]:
    async with httpx.AsyncClient(timeout=None) as client:
        content = await req.body()
        resp = (
            await client.post(url, content=content, headers=req.headers)
        ).raise_for_status()
        infer_resp = InferResponse.model_validate_json(resp.content)

        return infer_resp.code, Response(content=resp.content, headers=resp.headers)


@router.post("/image")
async def old_replace_with_reference(
    req: Request,
    ses: deps.UserSession,
    db: deps.Database,
    conf: deps.Config,
) -> Response:

    async with query_valid_subscription(ses.uid, db) as subscription:
        url = conf.infer.base + conf.infer.replace_any
        code, resp = await forward_to_infer_srv(url, req)
        if code == 0:
            subscription.remains -= 10
            subscription.utime = datetime.now()
            logger.info(f"reduce user {ses.nickname} magic points.")

        return resp

@router.post("/replace_any")
async def replace_with_any(
    req: Request,
    ses: deps.UserSession,
    db: deps.Database,
    conf: deps.Config,
) -> Response:

    async with query_valid_subscription(ses.uid, db) as subscription:
        url = conf.infer.base + conf.infer.replace_reference
        code, resp = await forward_to_infer_srv(url, req)
        if code == 0:
            subscription.remains -= 10
            subscription.utime = datetime.now()
            logger.info(f"reduce user {ses.nickname} magic points.")

        return resp
    
@router.post("/replace_with_reference")
async def replace_with_reference(
    req: Request,
    ses: deps.UserSession,
    db: deps.Database,
    conf: deps.Config,
) -> Response:

    async with query_valid_subscription(ses.uid, db) as subscription:
        url = conf.infer.base + conf.infer.replace_any
        code, resp = await forward_to_infer_srv(url, req)
        if code == 0:
            subscription.remains -= 10
            subscription.utime = datetime.now()
            logger.info(f"reduce user {ses.nickname} magic points.")

        return resp


@router.post("/image2video")
async def make_i2v_process(
    req: Request, ses: deps.UserSession, db: deps.Database, conf: deps.Config
) -> Response:

    async with query_valid_subscription(ses.uid, db) as subscription:
        url = conf.infer.base + conf.infer.image_to_video
        code, resp = await forward_to_infer_srv(url, req)
        if code == 0:
            subscription.remains -= 10
            subscription.utime = datetime.now()
            logger.info(f"reduce user {ses.nickname} magic points.")

        return resp


@router.post("/segment_any")
async def segment_any(
    req: Request,
    ses: deps.UserSession,
    db: deps.Database,
    conf: deps.Config,
) -> Response:

    async with query_valid_subscription(ses.uid, db) as subscription:
        url = conf.infer.base + conf.infer.segment_any
        code, resp = await forward_to_infer_srv(url, req)
        if code == 0:
            subscription.remains -= 10
            subscription.utime = datetime.now()
            logger.info(f"reduce user {ses.nickname} magic points.")

        return resp
