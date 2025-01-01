from flask import Blueprint

bp = Blueprint("auth", __name__)

from app.auth import routes as routes
from app.auth import wrappers as wrappers
