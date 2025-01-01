from flask import Blueprint

bp = Blueprint("auth", __name__)

from app.auth import routes, wrappers  # noqa: E402,F401
