from pydantic import BaseModel, ValidationError
from sqlmodel import Session, select
from ...models.db import MagicPointSubscription, SubscriptionType
from datetime import datetime
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi.routing import APIRoute
from fastapi import Request, Response
from typing import Any, Callable, Coroutine
import httpx
from loguru import logger
from fastapi.responses import JSONResponse


# Exception raised when user try call infer API but do not have enough points.
class NoPointError(Exception):
    def __init__(self, uid: int) -> None:
        self.uid = uid


# Exception raise when try get response no wait but request still in progress.
class NotDownError(Exception):

    def __init__(self, tid: str) -> None:
        self.tid: str = tid

    def __str__(self) -> str:
        return f"request {self.tid} still in progress."


# Exception raise when background request canceled.
class CancelError(Exception):
    def __init__(self, tid: str) -> None:
        self.tid: str = tid


# Model use to prase infer API response, just check response code.
class InferResponse(BaseModel):
    code: int


# query current uesr subscription from database.
async def get_current_subscription(uid: int, db: Session) -> MagicPointSubscription:
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

    return subscription


# Class use to manage magic point, just wrapper subscription model and some functions.
class PointManager:

    def __init__(self, subscription: MagicPointSubscription, db: Session) -> None:
        self._sub: MagicPointSubscription = subscription
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
            except NotDownError as exc:
                logger.warning(f"background request not complete yet, tid: {exc.tid}")
                return JSONResponse(content={"code": 10, "msg": str(exc)})

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

            # Raise when try to get background request from dict but no such key.
            except KeyError as exc:
                logger.info(f"index error: uid or tid '{str(exc)}' no in dict.")
                return JSONResponse(
                    content={"code": 4, "msg": "no such background request."}
                )

            except CancelError as exc:
                return JSONResponse(
                    content={"code": 5, "msg": f"task {exc.tid} has been canceled"}
                )

        return route_handler
