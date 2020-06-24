from flask import Blueprint

bp = Blueprint("user", __name__)

from app.user import routes  # noqa: F401
