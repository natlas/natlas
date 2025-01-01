from dateutil import parser
from flask import Blueprint

bp = Blueprint("filters", __name__)


@bp.app_template_filter("ctime")
def ctime(s, human=False):  # type: ignore[no-untyped-def]
    if human:
        return parser.parse(s).strftime("%Y-%m-%d %H:%M:%S %Z")
    return parser.parse(s).strftime("%Y-%m-%d %H:%M")


@bp.app_template_filter("get_screenshot_path")
def get_screenshot_path(inhash: str, service: str = "HTTP"):  # type: ignore[no-untyped-def]
    ext_map = {"HTTP": ".png", "HTTPS": ".png", "VNC": ".jpg"}

    return f"{inhash[0:2]}/{inhash[2:4]}/{inhash}{ext_map[service]}"
