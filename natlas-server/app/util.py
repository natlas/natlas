from datetime import datetime, timezone
import random


def utcnow_tz():
	return datetime.now(timezone.utc)


def generate_hex_16():
	return "%x" % random.randrange(16**16)


def generate_hex_32():
	return "%x" % random.randrange(16**32)


def pretty_time_delta(delta):
	hours, seconds = divmod(delta.seconds, 3600)
	minutes, seconds = divmod(seconds, 60)
	daystr = (str(delta.days) + "d, ") if delta.days else ""
	hourstr = (str(hours) + "h, ") if hours else ""
	minstr = (str(minutes) + "m, ") if minutes else ""
	secstr = str(seconds) + "s"
	return daystr + hourstr + minstr + secstr
