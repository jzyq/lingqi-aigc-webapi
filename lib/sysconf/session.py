from database.config import SystemConfigCategory as Category, SystemConfig
from sqlmodel import Session as DbSession, select
from sqlalchemy import Engine
import json

_DEFAULT_TTL = 3600


class Session:

    def __init__(self, db: Engine) -> None:
        self._db: Engine = db

    @property
    def ttl(self) -> int:
        with DbSession(self._db) as ses:
            query = (
                select(SystemConfig)
                .where(SystemConfig.category == Category.session)
                .where(SystemConfig.name == "ttl")
            )
            conf = ses.exec(query).one_or_none()

            if conf is None:
                return _DEFAULT_TTL

            return json.loads(conf.value)["ttl_in_seconds"]

    @ttl.setter
    def ttl(self, t: int) -> None:
        pass
        