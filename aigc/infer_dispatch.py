import json
import secrets
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Mapping

import httpx
from sqlalchemy import Engine
from sqlmodel import Session, select, asc
from loguru import logger
from pydantic import BaseModel
import time
import asyncio

from .models.database import inference, subscription

TOKEN_LEN = 8
RESPONSE_UNSET = "response_unset"
STREAM_NAME = "aigc:inference:stream"
READGROUP_NAME = "aigc:inference:stream:rg"
CONSUMER_NAME = "aigc:inference:dispatc:server"
INFERENCE_STATE_CHANNEL = "aigc:inference:state:notify"


class NotDownError(Exception):

    def __init__(self, tid: str) -> None:
        self.tid: str = tid

    def __str__(self) -> str:
        return f"inference {self.tid} is working in progress"


class CancelError(Exception):
    pass


class InferenceStateUpdateMessage(BaseModel):
    tid: str
    uid: int
    state: inference.State


class NewInferenceMessage(BaseModel):
    tid: str
    uid: int
    url: str


# query current uesr subscription from database.
@contextmanager
def current_subscription(uid: int, db: Engine) -> Iterator[subscription.Subscription]:
    query = (
        select(subscription.Subscription)
        .where(subscription.Subscription.uid == uid)
        .where(subscription.Subscription.expired == False)
    )

    with Session(db) as session:
        user_subscriptions = session.exec(query).all()

    trail: list[subscription.Subscription] = []
    payed: list[subscription.Subscription] = []

    for s in user_subscriptions:
        if s.stype == subscription.Type.trail:
            trail.append(s)
        if s.stype == subscription.Type.subscription:
            payed.append(s)

    s: subscription.Subscription | None = None
    if len(payed) != 0:
        s = payed[0]
    elif len(trail) != 0:
        s = trail[0]
    else:
        raise AssertionError("no valid subscriptions")

    try:
        yield s
    except:
        pass
    else:
        with Session(db) as session:
            session.add(s)
            session.commit()


class Client:

    def __init__(self, db: Engine) -> None:
        self._db: Engine = db

    async def new_inference(
        self,
        type: inference.Type,
        uid: int,
        url: str,
        point: int,
        body: Mapping[str, Any],
    ) -> str:
        token = secrets.token_hex(TOKEN_LEN)

        with Session(self._db) as session:
            log = inference.Log(
                uid=uid,
                tid=token,
                type=type,
                request=json.dumps(body),
                point=point,
                url=url,
            )
            session.add(log)
            session.commit()

        with current_subscription(uid, self._db) as subscription:
            subscription.remains -= point

        logger.info(f"new inference {token}")
        return token

    async def state(self, uid: int, tid: str) -> inference.State:
        with Session(self._db) as session:
            query = (
                select(inference.Log)
                .where(inference.Log.uid == uid)
                .where(inference.Log.tid == tid)
            )
            log = session.exec(query).one_or_none()
        if log is None:
            raise KeyError("no such inference")
        return log.state

    async def result(self, uid: int, tid: str) -> Mapping[str, Any]:
        with Session(self._db) as session:
            query = (
                select(inference.Log)
                .where(inference.Log.uid == uid)
                .where(inference.Log.tid == tid)
            )
            log = session.exec(query).one_or_none()

        if log is None:
            raise KeyError("no such inference")
        if log.response == "":
            raise NotDownError(tid)
        return json.loads(log.response)

    async def wait(self, uid: int, tid: str) -> Mapping[str, Any]:

        with Session(self._db) as session:
            query = (
                select(inference.Log)
                .where(inference.Log.uid == uid)
                .where(inference.Log.tid == tid)
            )
            log = session.exec(query).one_or_none()

            if log is None:
                raise KeyError("no such inference")

            if log.response != "":
                return json.loads(log.response)

        def do_wait(ilog: inference.Log):
            while True:
                time.sleep(1)
                with Session(self._db) as ses:
                    ses.add(ilog)
                    ses.refresh(ilog)

                    if ilog.state not in (
                        inference.State.waiting,
                        inference.State.in_progress,
                    ):
                        return

        await asyncio.to_thread(do_wait, log)

        with Session(self._db) as ses:
            ses.add(log)
            ses.refresh(log)

        if log.response == "":
            raise NotDownError(log.tid)

        return json.loads(log.response)

    async def cancel(self, uid: int, tid: str) -> None:
        with Session(self._db) as session:
            query = (
                select(inference.Log)
                .where(inference.Log.uid == uid)
                .where(inference.Log.tid == tid)
            )
            log = session.exec(query).one_or_none()

            if log is None:
                raise KeyError("no such inference")

            if log.state != inference.State.waiting:
                if log.state == inference.State.in_progress:
                    raise CancelError(f"inference {tid} already in progress")
                else:
                    raise CancelError(f"inference {tid} already complete")

            log.state = inference.State.canceled
            resp: dict[str, int | str] = {
                "code": 20,
                "msg": "inference has been canceled",
            }
            log.response = json.dumps(resp)
            log.utime = datetime.now()
            session.commit()

            with current_subscription(uid, self._db) as subscription:
                subscription.remains += log.point


class Server:

    def __init__(self, db: Engine) -> None:
        self._db: Engine = db

    def dispatch(self, log: inference.Log) -> None:

        with Session(self._db) as session:
            session.add(log)
            session.refresh(log)

            if log.state == inference.State.canceled:
                return

            log.state = inference.State.in_progress
            log.utime = datetime.now()
            session.add(log)
            session.commit()
            session.refresh(log)

            url = log.url
            body = json.loads(log.request)
            tid = log.tid

        try:
            with httpx.Client(timeout=None) as client:
                resp = client.post(url=url, json=body)
                resp.raise_for_status()

                log.response = resp.content.decode()
                log.state = inference.State.down
                log.utime = datetime.now()

            with Session(self._db) as session:
                session.add(log)
                session.commit()

            logger.info(f"inference {tid} complete.")

        except httpx.HTTPError as e:
            response = json.dumps({"code": 1, "msg": f"inference error, {str(e)}"})

            log.response = response
            log.state = inference.State.failed
            log.utime = datetime.now()

            with Session(self._db) as session:
                session.add(log)
                session.commit()

            with current_subscription(log.uid, self._db) as s:
                s.remains += log.point

            logger.error(
                f"inference {log.tid} error, {str(e)}, recharge point {log.point}"
            )

    def serve_forever(self) -> None:
        while True:
            query = (
                select(inference.Log)
                .where(inference.Log.state == inference.State.waiting)
                .order_by(asc(inference.Log.ctime))
                .limit(10)
            )
            with Session(self._db) as session:
                waiting_inference = session.exec(query).all()

            for i in waiting_inference:
                self.dispatch(i)
                time.sleep(1)
