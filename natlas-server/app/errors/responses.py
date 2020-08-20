from flask import Response, render_template

from .errors import NatlasServiceError


def json_response(err: NatlasServiceError) -> Response:
    return Response(
        err.get_json(), err.status_code, content_type="application/json; charset=utf-8"
    )


def html_response(err: NatlasServiceError) -> Response:
    return Response(render_template(err.template, err=err), err.status_code)


# This belongs below the function definitions due to Python's line-by-line interpretation
supported_formats = {"text/html": html_response, "application/json": json_response}


def get_response(requested_format: str, err: NatlasServiceError) -> Response:
    return supported_formats.get(requested_format)(err)


def get_supported_formats() -> list:
    return supported_formats.keys()
