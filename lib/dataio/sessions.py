from pydantic import BaseModel, computed_field
from datetime import datetime, timezone, timedelta
from models import session


class Session(BaseModel):

    def __init__(self, _mtk: session.Session) -> None:
        self._mtk: session.Session = _mtk

    @computed_field
    @property
    def token(self) -> str:
        return str(self._mtk.id)

    @computed_field
    @property
    def uid(self) -> int:
        return int(self._mtk.uid)

    @computed_field
    @property
    def nickname(self) -> str:
        return self._mtk.nickname

    @computed_field
    @property
    def login_time(self) -> datetime:
        return self._mtk.login_time

    @computed_field
    @property
    def update_time(self) -> datetime:
        return self._mtk.update_time

    @staticmethod
    async def new(
        uid: int, nickname: str, login_time: datetime | None = None, ttl: int = 3600
    ) -> "Session":
        ses = await session.Session.find(
            session.Session.uid == str(uid)
        ).first_or_none()
        if ses:
            return Session(_mtk=ses)

        dt = login_time if login_time else datetime.now()
        ses = session.Session(
            uid=str(uid),
            nickname=nickname,
            login_time=dt,
            update_time=dt,
            expire_in=ttl,
            expires=dt.astimezone(timezone.utc) + timedelta(seconds=ttl),
        )
        await ses.save()
        return Session(_mtk=ses)

    @staticmethod
    async def get(token: str) -> "Session | None":
        ses = await session.Session.get(token)
        if not ses:
            return None
        return Session(_mtk=ses)

    @staticmethod
    async def find_by_uid(uid: int) -> "Session | None":
        ses = await session.Session.find(
            session.Session.uid == str(uid)
        ).first_or_none()
        if not ses:
            return None
        return Session(_mtk=ses)

    async def refresh(self, ttl: int | None = None) -> None:
        if ttl:
            self._mtk.expire_in = ttl

        dt = datetime.now()
        self._mtk.update_time = dt
        self._mtk.expires = (dt + timedelta(seconds=self._mtk.expire_in)).astimezone(
            timezone.utc
        )
        await self._mtk.save()

    async def delete(self) -> None:
        await self._mtk.delete()
