from sqlalchemy import Engine
from sqlmodel import Session, select
from database.config import SystemConfigCategory as Category, SystemConfig


class SysConf:

    def __init__(self, db: Engine) -> None:
        self._db: Engine = db

    def get(self, category: Category, name: str) -> str | None:
        query = (
            select(SystemConfig)
            .where(SystemConfig.category == category)
            .where(SystemConfig.name == name)
        )

        with Session(self._db) as ses:
            conf = ses.exec(query).one_or_none()
            if conf:
                return conf.value
            else:
                return None

    def set(self, category: Category, name: str, value: str) -> None:
        query = (
            select(SystemConfig)
            .where(SystemConfig.category == category)
            .where(SystemConfig.name == name)
        )

        with Session(self._db) as ses:
            conf = ses.exec(query).one_or_none()
            if not conf:
                conf = SystemConfig(category=category, name=name, value=value)
            else:
                conf.value = value

            ses.add(conf)
            ses.commit()


class SysConfWithCategory:

    def __init__(self, db: Engine, category: Category) -> None:
        self._sysconf = SysConf(db)
        self._category = category

    def get(self, name: str) -> str | None:
        return self._sysconf.get(self._category, name)

    def set(self, name: str, value: str) -> None:
        return self._sysconf.set(self._category, name, value)
