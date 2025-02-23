from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

from natlas.accounts.models import User


def ensure_user(user: User | AnonymousUser) -> User:
    if not isinstance(user, User):
        raise PermissionDenied("You do not have permission to access this resource.")
    return User
