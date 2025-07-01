from datetime import datetime, tzinfo, timedelta


class TZ(tzinfo):

    def dst(self, dt: datetime | None) -> timedelta | None:
        return timedelta(0)

    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return timedelta(hours=8)


def format_datetime(dt: datetime) -> str:
    return dt.replace(microsecond=0, tzinfo=TZ()).isoformat()


def parse_datetime(dtstr: str) -> datetime:
    return datetime.fromisoformat(dtstr)
