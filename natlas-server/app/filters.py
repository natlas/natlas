from flask import Blueprint
from dateutil import parser

bp = Blueprint("filters", __name__)


@bp.app_template_filter("ctime")
def ctime(s, human=False):
    if human:
        return parser.parse(s).strftime("%Y-%m-%d %H:%M:%S %Z")
    return parser.parse(s).strftime("%Y-%m-%d %H:%M")


@bp.app_template_filter("get_screenshot_path")
def get_screenshot_path(inhash: str, service: str = "HTTP"):
    ext_map = {"HTTP": ".png", "HTTPS": ".png", "VNC": ".jpg"}

    return f"{inhash[0:2]}/{inhash[2:4]}/{inhash}{ext_map[service]}"
