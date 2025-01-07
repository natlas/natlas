from flask import redirect, url_for
from werkzeug.wrappers.response import Response


def get_scope_redirect(type: str) -> Response:
    redirects = {
        "scope": url_for("admin.scope"),
        "blacklist": url_for("admin.blacklist"),
        "default": url_for("admin.admin"),
    }
    return redirect(redirects.get(type, "default"))
