from typing import Annotated, Generator, Callable
from fastapi import Depends, Request, FastAPI, HTTPException
from sqlmodel import Session
from .wx import secret, client
from sqlalchemy import Engine
import redis.asyncio as redis
from . import common, sessions, config
import csv
from loguru import logger


def set_db_session_deps(app: FastAPI, engine: Engine):
    app.state.engine = engine


def set_wx_client_deps(app: FastAPI, secret: secret.WxSecrets):
    wx_client = client.new_client(secerts=secret)
    app.state.wx_client = wx_client


def set_rdb_deps(app: FastAPI, rdb: redis.Redis):
    app.state.rdb = rdb


def get_session(req: Request) -> Generator[Session, None, None]:
    with Session(req.app.state.engine) as s:
        yield s


def get_wx_client(req: Request) -> client.WxClient:
    return req.app.state.wx_client


def get_rdb(req: Request) -> redis.Redis:
    return req.app.state.rdb


def get_auth_token(authorization: common.HeaderField) -> str:
    auth_type, token = authorization.split(" ")
    if auth_type != "bearer" or token == "":
        raise HTTPException(
            status_code=401, detail="no valid authorization to access.")
    return token


def get_subscriptions_plan() -> Callable[[], list[config.SubscriptionPlan]]:
    conf = config.Config()
    subscriptions: list[config.SubscriptionPlan] = []

    # Read subscription plan config file.
    with open(conf.subscriptions_plan_file, 'r') as fp:
        plans = csv.reader(fp)
        for (price_str, month_str, point_each_day) in plans:
            try:
                subplan = config.SubscriptionPlan(
                    price=int(price_str), month=int(month_str), point_each_day=int(point_each_day))
                subscriptions.append(subplan)
            except ValueError:
                continue

    logger.info(
        f"load subscription plans, {len(subscriptions)} subscription plans:")
    for plan in subscriptions:
        logger.info(
            f"{plan.price / 100} CNY for {plan.month} month, {plan.point_each_day} points each day.")

    def getter() -> list[config.SubscriptionPlan]:
        return subscriptions
    return getter


Database = Annotated[Session, Depends(get_session)]

WxClient = Annotated[client.WxClient, Depends(get_wx_client)]

Rdb = Annotated[redis.Redis, Depends(get_rdb)]

AuthToken = Annotated[str, Depends(get_auth_token)]

SubscriptionPlan = Annotated[list[config.SubscriptionPlan], Depends(
    get_subscriptions_plan())]


async def get_user_session(rdb: Rdb, token: AuthToken) -> sessions.Session:
    ses = await sessions.get_session_or_none(rdb, token)
    if ses is None:
        raise HTTPException(
            status_code=401, detail="no valid authorization to access.")
    return ses

UserSession = Annotated[sessions.Session, Depends(get_user_session)]
