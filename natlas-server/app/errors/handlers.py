from flask import request
from app.errors import bp
from app import db
import elasticsearch
import sentry_sdk

from .errors import NatlasServiceError, NatlasSearchError
from .responses import get_response, get_supported_formats


def build_response(err: NatlasServiceError):
    selected_format = request.accept_mimetypes.best_match(
        get_supported_formats(), default="application/json"
    )
    return get_response(selected_format, err)


@bp.app_errorhandler(400)
def bad_request(e):
    errmsg = "The server was unable to process your request"
    err = NatlasServiceError(400, errmsg)
    return build_response(err)


@bp.app_errorhandler(404)
def page_not_found(e):
    errmsg = f"{request.path} Not found"
    err = NatlasServiceError(404, errmsg)
    return build_response(err)


@bp.app_errorhandler(405)
def method_not_allowed(e):
    errmsg = f"Method {request.method} Not Allowed on {request.path}"
    err = NatlasServiceError(405, errmsg)
    return build_response(err)


@bp.app_errorhandler(500)
def internal_server_error(e):
    errmsg = "Internal Server Error"
    err = NatlasServiceError(500, errmsg)
    db.session.rollback()
    return build_response(err)


@bp.app_errorhandler(elasticsearch.ConnectionError)
def elastic_unavailable(e):
    """
    This capture_exception happens here but not in others because
    the others use Flask's exception handling already. Since we are handling
    a specific exception class, we have to capture it explicitly.
    """
    errmsg = "Service Temporarily Unavailable"
    err = NatlasServiceError(503, errmsg)
    sentry_sdk.capture_exception(e)
    return build_response(err)


@bp.app_errorhandler(NatlasSearchError)
def invalid_elastic_query(e):
    sentry_sdk.capture_exception(e)
    return build_response(e)
