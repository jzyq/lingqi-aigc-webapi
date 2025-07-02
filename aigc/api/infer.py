from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, ValidationError
from sqlmodel import Session, select

from .. import deps
from ..models.db import MagicPointSubscription, SubscriptionType

app = FastAPI(title="Infer App")


class NoPointError(Exception):
    def __init__(self, uid: int) -> None:
        self.uid = uid


class InferResponse(BaseModel):
    code: int


@asynccontextmanager
async def query_valid_subscription(uid: int, db: Session) -> AsyncIterator[MagicPointSubscription]:
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
    except Exception as e:
        logger.error(repr(e))
        raise
    else:
        db.commit()
        logger.info(f"reduce user {uid} magic points.")


async def forward_to_infer_srv(url: str, req: Request) -> tuple[int, Response]:
    async with httpx.AsyncClient(timeout=None) as client:
        content = await req.body()
        resp = (await client.post(url, content=content, headers=req.headers)).raise_for_status()
        infer_resp = InferResponse.model_validate_json(resp.content)

        return infer_resp.code, Response(content=resp.content, headers=resp.headers)


# HTTPStatusError will raise when forward to infer srver.
@app.exception_handler(httpx.HTTPStatusError)
async def handle_httpx_http_status_error(req: Request, exc: httpx.HTTPStatusError) -> JSONResponse:
    logger.error(f"infer server unavailable, {repr(exc)}")
    return JSONResponse(content={"code": 1, "msg": "infer server unavailable"})


# ValidationError will raise when try parse infer server response body to a json.
@app.exception_handler(ValidationError)
async def handle_validation_error(req: Request, exc: ValidationError) -> JSONResponse:
    logger.error(f"infer response invalid, {repr(exc)}")
    return JSONResponse(content={"code": 2, "msg": "infer response invalid"})


# NoPointError will raise when user do not have enough point but try infer some.
@app.exception_handler(NoPointError)
async def handle_no_point_error(req: Request, exc: NoPointError) -> JSONResponse:
    logger.info(f"user {exc.uid} do not have magic point")
    return JSONResponse(content={"code": 3, "msg": "magic point not enough"})


@app.post("/image")
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
        return resp


@app.post("/image2video")
async def make_i2v_process(
    req: Request, ses: deps.UserSession, db: deps.Database, conf: deps.Config
) -> Response:

    async with query_valid_subscription(ses.uid, db) as subscription:
        url = conf.infer.base + conf.infer.image_to_video
        code, resp = await forward_to_infer_srv(url, req)
        if code == 0:
            subscription.remains -= 10
            subscription.utime = datetime.now()
        return resp


@app.post(
    "/segment_any"
)
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
        return resp
