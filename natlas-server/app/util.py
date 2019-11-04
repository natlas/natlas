from datetime import datetime, timezone
import random


def utcnow_tz():
	return datetime.now(timezone.utc)


def generate_hex_16():
	return "%x" % random.randrange(16**16)


def generate_hex_32():
	return "%x" % random.randrange(16**32)
