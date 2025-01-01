import secrets
from datetime import UTC, datetime


def utcnow_tz():  # type: ignore[no-untyped-def]
    return datetime.now(UTC)


def generate_hex_16():  # type: ignore[no-untyped-def]
    # 8 bytes converted to two hex digits each
    return secrets.token_hex(8)


def generate_hex_32():  # type: ignore[no-untyped-def]
    # 16 bytes converted to two hex digits each
    return secrets.token_hex(16)


def pretty_time_delta(delta):  # type: ignore[no-untyped-def]
    hours, seconds = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    daystr = (str(delta.days) + "d, ") if delta.days else ""
    hourstr = (str(hours) + "h, ") if hours else ""
    minstr = (str(minutes) + "m, ") if minutes else ""
    secstr = str(seconds) + "s"
    return daystr + hourstr + minstr + secstr
