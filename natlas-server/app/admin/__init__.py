from flask import Blueprint

bp = Blueprint("admin", __name__)

from app.admin import routes  # noqa: E402,F401
