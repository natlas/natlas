from flask import Response, render_template

from app.errors.errors import NatlasServiceError


def json_response(err: NatlasServiceError) -> Response:
    return Response(
        err.get_json(), err.status_code, content_type="application/json; charset=utf-8"
    )


def html_response(err: NatlasServiceError) -> Response:
    return Response(render_template(err.template, err=err), err.status_code)


# This belongs below the function definitions due to Python's line-by-line interpretation
supported_formats = {"text/html": html_response, "application/json": json_response}


def get_response(requested_format: str, err: NatlasServiceError) -> Response:
    return supported_formats.get(requested_format)(err)  # type: ignore[misc]


def get_supported_formats() -> list:  # type: ignore[type-arg]
    return supported_formats.keys()  # type: ignore[return-value]
