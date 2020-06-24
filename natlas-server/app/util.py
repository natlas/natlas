from datetime import datetime, timezone
import secrets


def utcnow_tz():
    return datetime.now(timezone.utc)


def generate_hex_16():
    # 8 bytes converted to two hex digits each
    return secrets.token_hex(8)


def generate_hex_32():
    # 16 bytes converted to two hex digits each
    return secrets.token_hex(16)


def pretty_time_delta(delta):
    hours, seconds = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    daystr = (str(delta.days) + "d, ") if delta.days else ""
    hourstr = (str(hours) + "h, ") if hours else ""
    minstr = (str(minutes) + "m, ") if minutes else ""
    secstr = str(seconds) + "s"
    return daystr + hourstr + minstr + secstr
