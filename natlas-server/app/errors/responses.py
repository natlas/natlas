from flask import Response, render_template

from .http_error import HTTPError


def json_response(err: HTTPError) -> Response:
    return Response(
        err.get_json(), err.status_code, content_type="application/json; charset=utf-8"
    )


def html_response(err: HTTPError) -> Response:
    return Response(render_template(err.template, err=err), err.status_code)


# This belongs below the function definitions due to Python's line-by-line interpretation
supported_formats = {"text/html": html_response, "application/json": json_response}


def get_response(requested_format: str, err: HTTPError) -> Response:
    return supported_formats.get(requested_format)(err)


def get_supported_formats() -> list:
    return supported_formats.keys()
