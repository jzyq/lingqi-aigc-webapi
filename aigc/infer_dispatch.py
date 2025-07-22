import json
import secrets
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Mapping

import httpx
import redis
import redis.asyncio as async_redis
import redis.exceptions
import sqlalchemy
import sqlmodel
from loguru import logger
from pydantic import BaseModel

from . import models

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
    state: models.db.InferenceState


class NewInferenceMessage(BaseModel):
    tid: str
    uid: int
    url: str


# query current uesr subscription from database.
@contextmanager
def current_subscription(
    uid: int, db: sqlalchemy.Engine
) -> Iterator[models.db.MagicPointSubscription]:
    query = (
        sqlmodel.select(models.db.MagicPointSubscription)
        .where(models.db.MagicPointSubscription.uid == uid)
        .where(models.db.MagicPointSubscription.expired == False)
    )

    with sqlmodel.Session(db) as session:
        subscriptions = session.exec(query).all()

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

    try:
        yield subscription
    except:
        pass
    else:
        with sqlmodel.Session(db) as session:
            session.add(subscription)
            session.commit()


class Client:

    def __init__(self, rdb: async_redis.Redis, db: sqlalchemy.Engine) -> None:
        self._rdb = rdb
        self._db = db

    async def new_inference(
        self,
        type: models.db.InferenceType,
        uid: int,
        url: str,
        point: int,
        body: Mapping[str, Any],
    ) -> str:
        token = secrets.token_hex(TOKEN_LEN)

        with sqlmodel.Session(self._db) as session:
            inference = models.db.InferenceLog(
                uid=uid, tid=token, type=type, request=json.dumps(body), point=point
            )
            session.add(inference)
            session.commit()

        with current_subscription(uid, self._db) as subscription:
            subscription.remains -= point

        new_inference_message = NewInferenceMessage(tid=token, uid=uid, url=url)
        await self._rdb.xadd(STREAM_NAME, new_inference_message.model_dump())  # type: ignore

        logger.info(f"new inference {token}")
        return token

    async def state(self, uid: int, tid: str) -> models.db.InferenceState:
        with sqlmodel.Session(self._db) as session:
            query = (
                sqlmodel.select(models.db.InferenceLog)
                .where(models.db.InferenceLog.uid == uid)
                .where(models.db.InferenceLog.tid == tid)
            )
            inference = session.exec(query).one_or_none()
        if inference is None:
            raise KeyError("no such inference")
        return inference.state

    async def result(self, uid: int, tid: str) -> Mapping[str, Any]:
        with sqlmodel.Session(self._db) as session:
            query = (
                sqlmodel.select(models.db.InferenceLog)
                .where(models.db.InferenceLog.uid == uid)
                .where(models.db.InferenceLog.tid == tid)
            )
            inference = session.exec(query).one_or_none()

        if inference is None:
            raise KeyError("no such inference")
        if inference.response == "":
            raise NotDownError(tid)
        return json.loads(inference.response)

    async def wait(self, uid: int, tid: str) -> Mapping[str, Any]:
        pubsub = self._rdb.pubsub()  # type: ignore
        await pubsub.subscribe(INFERENCE_STATE_CHANNEL)  # type: ignore

        with sqlmodel.Session(self._db) as session:
            query = (
                sqlmodel.select(models.db.InferenceLog)
                .where(models.db.InferenceLog.uid == uid)
                .where(models.db.InferenceLog.tid == tid)
            )
            inference = session.exec(query).one_or_none()

            if inference is None:
                raise KeyError("no such inference")

            if inference.response != "":
                return json.loads(inference.response)

        while True:
            msg = await pubsub.get_message(  # type: ignore
                ignore_subscribe_messages=True, timeout=1
            )
            if msg and msg["type"] == "message":
                update_message = InferenceStateUpdateMessage.model_validate_json(
                    msg["data"]  # type: ignore
                )
                if (
                    update_message.tid == inference.tid
                    and update_message.uid == inference.uid
                ):
                    if update_message.state not in (
                        models.db.InferenceState.waiting,
                        models.db.InferenceState.in_progress,
                    ):
                        break

        with sqlmodel.Session(self._db) as session:
            session.add(inference)
            session.refresh(inference)

            return json.loads(inference.response)

    async def cancel(self, uid: int, tid: str) -> None:
        with sqlmodel.Session(self._db) as session:
            query = (
                sqlmodel.select(models.db.InferenceLog)
                .where(models.db.InferenceLog.uid == uid)
                .where(models.db.InferenceLog.tid == tid)
            )
            inference = session.exec(query).one_or_none()

            if inference is None:
                raise KeyError("no such inference")

            if inference.state != models.db.InferenceState.waiting:
                if inference.state == models.db.InferenceState.in_progress:
                    raise CancelError(f"inference {tid} already in progress")
                else:
                    raise CancelError(f"inference {tid} already complete")

            inference.state = models.db.InferenceState.canceled
            resp: dict[str, int | str] = {
                "code": 20,
                "msg": "inference has been canceled",
            }
            inference.response = json.dumps(resp)
            inference.utime = datetime.now()
            session.commit()

            with current_subscription(uid, self._db) as subscription:
                subscription.remains += inference.point

            await self._rdb.publish(  # type: ignore
                INFERENCE_STATE_CHANNEL, json.dumps({"uid": uid, "tid": tid})
            )


class Server:

    def __init__(self, rdb: redis.Redis, db: sqlalchemy.Engine) -> None:
        self._rdb = rdb
        self._db = db

    def dispatch(self, tid: str, uid: int, url: str) -> None:

        with sqlmodel.Session(self._db) as session:
            query = (
                sqlmodel.select(models.db.InferenceLog)
                .where(models.db.InferenceLog.uid == uid)
                .where(models.db.InferenceLog.tid == tid)
            )
            inference = session.exec(query).one()

            if inference.state != models.db.InferenceState.waiting:
                logger.info(
                    f"inference {tid} has been canceled or already complete, ignore."
                )
                return

            inference.state = models.db.InferenceState.in_progress
            inference.utime = datetime.now()
            session.commit()

            try:
                with httpx.Client(timeout=None) as client:
                    resp = client.post(url=url, json=json.loads(inference.request))
                    resp.raise_for_status()

                    inference.response = resp.content.decode()
                    inference.state = models.db.InferenceState.down
                    inference.utime = datetime.now()
                    session.commit()

                update_message = InferenceStateUpdateMessage(
                    tid=tid, uid=uid, state=models.db.InferenceState.down
                )
                self._rdb.publish(  # type: ignore
                    INFERENCE_STATE_CHANNEL, update_message.model_dump_json()
                )
                logger.info(f"inference {tid} complete.")

            except httpx.HTTPError as e:
                response = json.dumps({"code": 1, "msg": f"inference error, {str(e)}"})

                inference.response = response
                inference.state = models.db.InferenceState.failed
                inference.utime = datetime.now()
                session.commit()

                with current_subscription(inference.uid, self._db) as subscription:
                    subscription.remains += inference.point

                update_message = InferenceStateUpdateMessage(
                    tid=tid, uid=uid, state=models.db.InferenceState.failed
                )
                self._rdb.publish(  # type: ignore
                    INFERENCE_STATE_CHANNEL, update_message.model_dump_json()
                )

                logger.error(
                    f"inference {tid} error, {str(e)}, recharge point {inference.point}"
                )

    def serve_forever(self) -> None:
        try:
            self._rdb.xgroup_create(STREAM_NAME, READGROUP_NAME, mkstream=True)
        except:
            pass

        while True:
            try:
                messages = self._rdb.xreadgroup(
                    READGROUP_NAME, CONSUMER_NAME, {STREAM_NAME: ">"}, block=30 * 1000
                )
            except redis.exceptions.ResponseError as exc:
                logger.warning(f"poll message error: {str(exc)}")
                try:
                    self._rdb.xgroup_create(STREAM_NAME, READGROUP_NAME, mkstream=True)
                except:
                    pass
                continue

            if len(messages) == 0:  # type: ignore
                continue

            logger.debug(messages)
            stream_name, messages = messages[0]  # type:ignore
            if stream_name != STREAM_NAME:
                continue

            for mid, data in messages:  # type: ignore
                new_inference = NewInferenceMessage.model_validate(data)
                logger.info(
                    f"new inference {new_inference.tid} from user {new_inference.uid}"
                )
                self.dispatch(
                    tid=new_inference.tid, uid=new_inference.uid, url=new_inference.url
                )
                self._rdb.xack(STREAM_NAME, READGROUP_NAME, mid)  # type: ignore
