from django.core.exceptions import ValidationError
from email_validator import EmailNotValidError, ValidatedEmail, validate_email


def validate_deliverable_email(email: str) -> ValidatedEmail:
    try:
        return validate_email(email, check_deliverability=True)
    except EmailNotValidError as e:
        raise ValidationError(str(e)) from e
