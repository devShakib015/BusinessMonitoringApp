"""Timestamps.

The shop's computer clock is the source of truth: a shopkeeper reading a
day-end report means *their* day, and the till is not shared across
timezones.  Storing local time keeps date-range reports simple and keeps the
stored value readable when someone opens the database directly.
"""

from datetime import date, datetime, timedelta

STAMP = "%Y-%m-%d %H:%M:%S"
DATE = "%Y-%m-%d"


def now() -> datetime:
    return datetime.now()


def stamp(moment: datetime | None = None) -> str:
    return (moment or datetime.now()).strftime(STAMP)


def today() -> str:
    return date.today().strftime(DATE)


def parse(value: str | None) -> datetime | None:
    if not value:
        return None
    for pattern in (STAMP, "%Y-%m-%d %H:%M:%S.%f", DATE):
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            continue
    return None


def pretty(value: str | None, with_time: bool = True) -> str:
    moment = parse(value)
    if not moment:
        return value or ""
    return moment.strftime("%d %b %Y, %I:%M %p" if with_time else "%d %b %Y")


def day_bounds(day: date) -> tuple[str, str]:
    """Inclusive-exclusive timestamp bounds covering a single day."""
    start = datetime.combine(day, datetime.min.time())
    return start.strftime(STAMP), (start + timedelta(days=1)).strftime(STAMP)


def range_bounds(start: date, end: date) -> tuple[str, str]:
    """Inclusive-exclusive bounds covering ``start``..``end`` inclusive."""
    begin = datetime.combine(start, datetime.min.time())
    finish = datetime.combine(end, datetime.min.time()) + timedelta(days=1)
    return begin.strftime(STAMP), finish.strftime(STAMP)
