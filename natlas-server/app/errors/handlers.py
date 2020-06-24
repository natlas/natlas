from flask import render_template
from app.errors import bp
from app import db
import elasticsearch
import sentry_sdk


@bp.app_errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404


@bp.app_errorhandler(405)
def method_not_allowed(e):
    return render_template("errors/405.html"), 405


@bp.app_errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    return render_template("errors/500.html"), 500


@bp.app_errorhandler(elasticsearch.ConnectionError)
def elastic_unavailable(e):
    sentry_sdk.capture_exception(e)
    return render_template("errors/503.html"), 503
