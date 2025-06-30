from typing import Annotated
from fastapi import Header
from datetime import datetime, tzinfo, timedelta
from .models import db
from sqlmodel import Session, select

HeaderField = Annotated[str, Header()]

class NotFoundError(Exception):
    pass


class TZ(tzinfo):

    def dst(self, dt: datetime | None) -> timedelta | None:
        return timedelta(0)

    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return timedelta(hours=8)


def format_datetime(dt: datetime) -> str:
    return dt.replace(microsecond=0, tzinfo=TZ()).isoformat()


def parse_datetime(dtstr: str) -> datetime:
    return datetime.fromisoformat(dtstr)


async def query_valid_subscription(
    uid: int, dbsession: Session
) -> db.MagicPointSubscription:
    query = (
        select(db.MagicPointSubscription)
        .where(db.MagicPointSubscription.uid == uid)
        .where(db.MagicPointSubscription.expired == False)
    )
    subscriptions = dbsession.exec(query).all()

    trail: list[db.MagicPointSubscription] = []
    payed: list[db.MagicPointSubscription] = []

    for s in subscriptions:
        if s.stype == db.SubscriptionType.trail:
            trail.append(s)
        if s.stype == db.SubscriptionType.subscription:
            payed.append(s)

    if len(payed) != 0:
        return payed[0]
    
    if len(trail) != 0:
        return trail[0]
    
    raise NotFoundError("no valid subscriptions")
