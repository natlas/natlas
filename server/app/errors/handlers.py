import elasticsearch
import sentry_sdk
from flask import Response, request

from app import db
from app.errors import bp
from app.errors.errors import NatlasSearchError, NatlasServiceError
from app.errors.responses import get_response, get_supported_formats


def build_response(err: NatlasServiceError) -> Response:
    selected_format = request.accept_mimetypes.best_match(
        get_supported_formats(), default="application/json"
    )
    return get_response(selected_format, err)


@bp.app_errorhandler(400)
def bad_request(e: object) -> Response:
    errmsg = "The server was unable to process your request"
    err = NatlasServiceError(400, errmsg)
    return build_response(err)


@bp.app_errorhandler(404)
def page_not_found(e: object) -> Response:
    errmsg = f"{request.path} Not found"
    err = NatlasServiceError(404, errmsg)
    return build_response(err)


@bp.app_errorhandler(405)
def method_not_allowed(e: object) -> Response:
    errmsg = f"Method {request.method} Not Allowed on {request.path}"
    err = NatlasServiceError(405, errmsg)
    return build_response(err)


@bp.app_errorhandler(500)
def internal_server_error(e: object) -> Response:
    errmsg = "Internal Server Error"
    err = NatlasServiceError(500, errmsg)
    db.session.rollback()
    return build_response(err)


@bp.app_errorhandler(elasticsearch.ConnectionError)
def elastic_unavailable(e: elasticsearch.ConnectionError) -> Response:
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
def invalid_elastic_query(e: NatlasSearchError) -> Response:
    sentry_sdk.capture_exception(e)
    return build_response(e)
