import json
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from flask import Response, abort, current_app, flash, redirect, request, url_for
from flask_login import current_user

from app import login as lm
from app.models import Agent

P = ParamSpec("P")
R = TypeVar("R")


# This can be used in lieu of @login_required for pages that don't require a user account
def is_authenticated(f: Callable[P, R]) -> Callable[P, R]:
    @wraps(f)
    def decorated_function(*args: P.args, **kwargs: P.kwargs) -> R:
        if current_app.config["LOGIN_REQUIRED"] and not current_user.is_authenticated:
            return lm.unauthorized()  # type: ignore[no-any-return]
        return f(*args, **kwargs)

    return decorated_function


# An explicit wrapper to make a route only available if a request is not authenticated
def is_not_authenticated(f: Callable[P, R]) -> Callable[P, R]:
    @wraps(f)
    def decorated_function(*args: P.args, **kwargs: P.kwargs) -> R:
        if current_user.is_authenticated:
            flash("You're already logged in!", "warning")
            return redirect(url_for("main.browse"))  # type: ignore[return-value]
        return f(*args, **kwargs)

    return decorated_function


# Ensure current user is an admin
def is_admin(f: Callable[P, R]) -> Callable[P, R]:
    @wraps(f)
    def decorated_function(*args: P.args, **kwargs: P.kwargs) -> R:
        if current_user.is_anonymous or not current_user.is_admin:
            return lm.unauthorized()  # type: ignore[no-any-return]
        return f(*args, **kwargs)

    return decorated_function


# Validate agent authentication if required
def is_agent_authenticated(f: Callable[P, R]) -> Callable[P, R]:
    @wraps(f)
    def decorated_function(*args: P.args, **kwargs: P.kwargs) -> R:
        # if we don't require agent authentication then don't bother
        if not current_app.config["AGENT_AUTHENTICATION"]:
            return f(*args, **kwargs)
        if not (
            request.headers.get("Authorization", None)
            and Agent.verify_agent(request.headers["Authorization"])
        ):
            status_code = 403
            response_body = json.dumps(
                {
                    "status": status_code,
                    "message": "Authorization is required to access this endpoint",
                    "retry": False,
                }
            )
            abort(
                Response(
                    response=response_body,
                    status=status_code,
                    content_type="application/json",
                )
            )
        return f(*args, **kwargs)

    return decorated_function
