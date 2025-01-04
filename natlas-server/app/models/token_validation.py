import secrets
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def default_validator() -> bool:
    # if no custom validator is supplied then just pass
    return True


def validate_token(
    record: T,
    provided_token: str,
    stored_token: str,
    validator: Callable[[], bool] = default_validator,
) -> T | None:
    if record and secrets.compare_digest(provided_token, stored_token) and validator():
        return record
    # still do a digest compare of equal sizes to resist timing attacks
    secrets.compare_digest(provided_token, "a" * len(provided_token))
    return None
