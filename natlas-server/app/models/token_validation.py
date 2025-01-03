import secrets


def default_validator():  # type: ignore[no-untyped-def]
    # if no custom validator is supplied then just pass
    return True


def validate_token(record, provided_token, stored_token, validator=default_validator):  # type: ignore[no-untyped-def]
    if record and secrets.compare_digest(provided_token, stored_token) and validator():
        return record
    # still do a digest compare of equal sizes to resist timing attacks
    secrets.compare_digest(provided_token, "a" * len(provided_token))
    return False
