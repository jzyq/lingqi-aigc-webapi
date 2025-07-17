import json
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from loguru import logger
from pydantic import BaseModel, ValidationError
from sqlalchemy import Engine
from sqlmodel import Session, select

from .. import config, deps, infer_dispatch, models, prompt_translate, sessions


# Exception raised when user try call infer API but do not have enough points.
class NoPointError(Exception):
    def __init__(self, uid: int) -> None:
        self.uid = uid


# Model use to prase infer API response, just check response code.
class InferResponse(BaseModel):
    code: int


# query current uesr subscription from database.
async def get_current_subscription(
    uid: int, db: Session
) -> models.db.MagicPointSubscription:
    query = (
        select(models.db.MagicPointSubscription)
        .where(models.db.MagicPointSubscription.uid == uid)
        .where(models.db.MagicPointSubscription.expired == False)
    )
    subscriptions = db.exec(query).all()

    trail: list[models.db.MagicPointSubscription] = []
    payed: list[models.db.MagicPointSubscription] = []

    for s in subscriptions:
        if s.stype == models.db.SubscriptionType.trail:
            trail.append(s)
        if s.stype == models.db.SubscriptionType.subscription:
            payed.append(s)

    subscription: models.db.MagicPointSubscription | None = None
    if len(payed) != 0:
        subscription = payed[0]
    elif len(trail) != 0:
        subscription = trail[0]
    else:
        raise AssertionError("no valid subscriptions")

    return subscription


# Class use to manage magic point, just wrapper subscription model and some functions.
class PointManager:

    def __init__(
        self, subscription: models.db.MagicPointSubscription, db: Session
    ) -> None:
        self._sub: models.db.MagicPointSubscription = subscription
        self._db: Session = db

    @property
    def magic_points(self) -> int:
        return self._sub.remains

    def deduct(self, point: int):
        self._sub.remains -= point
        self._sub.utime = datetime.now()
        self._db.commit()

    def recharge(self, point: int):
        self._sub.remains += point
        self._sub.utime = datetime.now()
        self._db.commit()


# Context manager wrap query subscription and deduct function.
@asynccontextmanager
async def point_manager(uid: int, db: Session) -> AsyncIterator[PointManager]:
    sub = await get_current_subscription(uid, db)
    mgr = PointManager(sub, db)

    yield mgr


# Custom route class use to handle exceptions raised during infer.
class InferRoute(APIRoute):

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original_route_handler = super().get_route_handler()

        async def route_handler(req: Request) -> Response:
            try:
                return await original_route_handler(req)

            # Raise when try get background request response but request still in progress.
            except infer_dispatch.NotDownError as exc:
                logger.warning(f"background request not complete yet, tid: {exc.tid}")
                return JSONResponse(content={"code": 10, "msg": str(exc)})

            except infer_dispatch.CancelError as exc:
                logger.warning(f"try cancel inference, {str(exc)}")
                return JSONResponse(content={"code": 11, "msg": str(exc)})

            # HTTPStatusError will raise when forward to infer srver.
            except httpx.HTTPError as exc:
                logger.error(f"infer server unavailable, {repr(exc)}")
                return JSONResponse(
                    content={
                        "code": 1,
                        "msg": f"infer server unavailable, exception: {repr(exc)}",
                    }
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

            # Raise when try to get background request from dict but no such key.
            except KeyError as exc:
                logger.info(f"index error: uid or tid '{str(exc)}' no in dict.")
                return JSONResponse(
                    content={"code": 4, "msg": "no such background request."}
                )

        return route_handler


# Normal response.
class APIResponse(BaseModel):
    code: int
    msg: str


# Response model when append new request and query requests state.
class GetStateResponse(APIResponse):
    tid: str
    index: int
    state: str


# Response model when create new background task.
class CreateRequestResponse(APIResponse):
    tid: str


# A dependence function to get a new point manager.
async def get_point_manager(
    ses: sessions.Session = Depends(deps.get_user_session),
    dbses: Session = Depends(deps.get_db_session),
) -> PointManager:

    sub = await get_current_subscription(ses.uid, dbses)
    mgr = PointManager(sub, dbses)
    return mgr


async def start_new_inference(
    type: models.db.InferenceType,
    uid: int,
    url: str,
    point: int,
    pm: PointManager,
    request_body: dict[str, Any],
    translator: prompt_translate.ZhipuaiClient,
    inference_client: infer_dispatch.Client,
) -> CreateRequestResponse:

    if pm.magic_points < point:
        raise NoPointError(uid)

    if "text_prompt" in request_body:
        request_body["text_prompt"] = translator.translate(request_body["text_prompt"])

    tid = await inference_client.new_inference(type, uid, url, point, request_body)

    return CreateRequestResponse(code=0, msg="ok", tid=tid)


# Define router
router = APIRouter(prefix="/async/infer", route_class=InferRoute)


# API to query background requests current state, no block.
@router.get("/{tid}/state")
async def get_req_state(
    tid: str,
    ses: deps.UserSession,
    db: Engine = Depends(deps.get_db_engine),
    inference_client: infer_dispatch.Client = Depends(deps.get_inference_client),
) -> GetStateResponse:

    response = GetStateResponse(
        code=0, msg="ok", tid=tid, index=0, state=str(models.db.InferenceState.waiting)
    )

    try:
        state = await inference_client.state(ses.uid, tid)
        response.state = str(state)

    except (ValueError, KeyError):
        with Session(db) as dbsession:
            ilog = dbsession.exec(
                select(models.db.InferenceLog)
                .where(models.db.InferenceLog.uid == ses.uid)
                .where(models.db.InferenceLog.tid == tid)
            ).one_or_none()

            if ilog is None:
                raise KeyError()

            response.state = str(ilog.state)

    return response


# API to get result of a request if have, no block.
@router.get("/{tid}/result")
async def get_req_result(
    tid: str,
    ses: deps.UserSession,
    inference_client: infer_dispatch.Client = Depends(deps.get_inference_client),
) -> JSONResponse:
    result = await inference_client.result(ses.uid, tid)
    return JSONResponse(content=result)


# API to long poll inference request result.
@router.get("/{tid}/result/wait")
async def wait_req_result(
    tid: str,
    ses: deps.UserSession,
    inference_client: infer_dispatch.Client = Depends(deps.get_inference_client),
) -> JSONResponse:
    resp = await inference_client.wait(ses.uid, tid)
    return JSONResponse(content=resp)


# API to cancel waiting request
@router.post("/{tid}/cancel")
async def cancel_waiting_request(
    tid: str,
    ses: deps.UserSession,
    inference_client: infer_dispatch.Client = Depends(deps.get_inference_client),
) -> APIResponse:

    await inference_client.cancel(ses.uid, tid)
    return APIResponse(code=0, msg="task canceled")


# API to create a background replace with any infer request.
@router.post("/replace_any")
async def replace_with_any(
    req: Request,
    ses: sessions.Session = Depends(deps.get_user_session),
    pm: PointManager = Depends(get_point_manager),
    conf: config.Config = Depends(config.get_config),
    translator: prompt_translate.ZhipuaiClient = Depends(deps.get_translator),
    inference_client: infer_dispatch.Client = Depends(deps.get_inference_client),
) -> CreateRequestResponse:
    point = 10
    url = conf.infer.base + conf.infer.replace_any
    return await start_new_inference(
        models.db.InferenceType.replace_with_any,
        ses.uid,
        url,
        point,
        pm,
        await req.json(),
        translator,
        inference_client,
    )


# API to create a background replace with reference infer request.
@router.post("/replace_with_reference")
async def replace_with_reference(
    req: Request,
    ses: deps.UserSession,
    pm: PointManager = Depends(get_point_manager),
    conf: config.Config = Depends(config.get_config),
    translator: prompt_translate.ZhipuaiClient = Depends(deps.get_translator),
    inference_client: infer_dispatch.Client = Depends(deps.get_inference_client),
) -> CreateRequestResponse:

    point = 10
    url = conf.infer.base + conf.infer.replace_reference
    return await start_new_inference(
        models.db.InferenceType.replace_with_reference,
        ses.uid,
        url,
        point,
        pm,
        await req.json(),
        translator,
        inference_client,
    )


# API to create a background image to video request.
@router.post("/image_to_video")
async def image_to_video(
    req: Request,
    ses: deps.UserSession,
    pm: PointManager = Depends(get_point_manager),
    conf: config.Config = Depends(config.get_config),
    translator: prompt_translate.ZhipuaiClient = Depends(deps.get_translator),
    inference_client: infer_dispatch.Client = Depends(deps.get_inference_client),
) -> CreateRequestResponse:
    point = 30
    url = conf.infer.base + conf.infer.image_to_video
    return await start_new_inference(
        models.db.InferenceType.image_to_video,
        ses.uid,
        url,
        point,
        pm,
        await req.json(),
        translator,
        inference_client,
    )


# API to create a background segment any infer request.
@router.post("/segment_any")
async def segment_any(
    req: Request,
    ses: deps.UserSession,
    pm: PointManager = Depends(get_point_manager),
    conf: config.Config = Depends(config.get_config),
    translator: prompt_translate.ZhipuaiClient = Depends(deps.get_translator),
    inference_client: infer_dispatch.Client = Depends(deps.get_inference_client),
) -> CreateRequestResponse:
    point = 1
    url = conf.infer.base + conf.infer.segment_any
    return await start_new_inference(
        models.db.InferenceType.segment_any,
        ses.uid,
        url,
        point,
        pm,
        await req.json(),
        translator,
        inference_client,
    )


# API to create a background edit with prompt infer request.
@router.post("/edit_with_prompt")
async def edit_with_prompt(
    req: Request,
    ses: deps.UserSession,
    pm: PointManager = Depends(get_point_manager),
    conf: config.Config = Depends(config.get_config),
    translator: prompt_translate.ZhipuaiClient = Depends(deps.get_translator),
    inference_client: infer_dispatch.Client = Depends(deps.get_inference_client),
) -> CreateRequestResponse:
    normal_mode_point = 10
    enhance_mode_point = 15

    try:
        req_body = await req.json()
        if "enhance" in req_body and req_body["enhance"] == True:
            point = enhance_mode_point
        else:
            point = normal_mode_point
    except json.JSONDecodeError:
        raise HTTPException(422, detail="must have request body")

    url = conf.infer.base + conf.infer.edit_with_prompt
    return await start_new_inference(
        models.db.InferenceType.edit_with_prompt,
        ses.uid,
        url,
        point,
        pm,
        req_body,
        translator,
        inference_client,
    )
