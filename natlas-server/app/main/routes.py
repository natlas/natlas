import elasticsearch
from flask import (
    Response,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user

from app.auth.forms import LoginForm, RegistrationForm
from app.auth.wrappers import is_authenticated
from app.errors import NatlasSearchError
from app.main import bp
from app.main.pagination import build_pagination_urls, results_offset


@bp.route("/")
def index() -> str:
    login_form = None
    reg_form = None
    if current_user.is_anonymous:
        if current_app.config["LOGIN_REQUIRED"]:
            login_form = LoginForm(prefix="login")
        if current_app.config["REGISTER_ALLOWED"]:
            reg_form = RegistrationForm(prefix="register")
    return render_template("main/index.html", login_form=login_form, reg_form=reg_form)


# Serve media files in case the front-end proxy doesn't do it
@bp.route("/media/<path:filename>")
@is_authenticated
def send_media(filename: str) -> Response:
    # If you're looking at this function, wondering why your files aren't sending...
    # It's probably because current_app.config['MEDIA_DIRECTORY'] isn't pointing to an absolute file path
    return send_from_directory(current_app.config["MEDIA_DIRECTORY"], filename)


@bp.route("/browse")
@is_authenticated
def browse() -> str:
    """
    A simple browser that doesn't deal with queries at all
    """
    page = int(request.args.get("page", 1))
    includeHistory = request.args.get("includeHistory", False)

    results_per_page, search_offset = results_offset(page)

    searchIndex = "history" if includeHistory else "latest"

    count, hostdata = current_app.elastic.search(  # type: ignore[attr-defined]
        results_per_page, search_offset, searchIndex=searchIndex
    )
    totalHosts = current_app.elastic.total_hosts()  # type: ignore[attr-defined]

    if includeHistory:
        next_url, prev_url = build_pagination_urls(
            "main.browse", page, count, includeHistory=includeHistory
        )
    else:
        # By using the if/else we can avoid putting includeHistory=False into the url that gets constructed
        next_url, prev_url = build_pagination_urls("main.browse", page, count)

    return render_template(
        "main/browse.html",
        numresults=count,
        totalHosts=totalHosts,
        page=page,
        hosts=hostdata,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/search")
@is_authenticated
def search() -> Response | str:
    """
    Return search results for a given query
    """
    query = request.args.get("query", "")
    if query == "":
        return redirect(url_for("main.browse"))  # type: ignore[return-value]
    page = int(request.args.get("page", 1))
    format = request.args.get("format", "")
    scan_ids = request.args.get("includeScanIDs", "")
    includeHistory = request.args.get("includeHistory", False)

    results_per_page, search_offset = results_offset(page)

    searchIndex = "history" if includeHistory else "latest"

    try:
        count, context = current_app.elastic.search(  # type: ignore[attr-defined]
            results_per_page, search_offset, query=query, searchIndex=searchIndex
        )
    except elasticsearch.RequestError as e:
        raise NatlasSearchError(e) from e

    totalHosts = current_app.elastic.total_hosts()  # type: ignore[attr-defined]

    if includeHistory:
        next_url, prev_url = build_pagination_urls(
            "main.search", page, count, query=query, includeHistory=includeHistory
        )
    else:
        next_url, prev_url = build_pagination_urls(
            "main.search", page, count, query=query
        )

    # what kind of output are we looking for?
    if format == "hostlist":
        hostlist = []
        for host in context:
            if scan_ids:
                hostlist.append(str(host["ip"]) + "," + str(host["scan_id"]))
            else:
                hostlist.append(str(host["ip"]))
        return Response("\n".join(hostlist), mimetype="text/plain")
    if format == "json":
        return jsonify(list(context))
    return render_template(
        "main/search.html",
        query=query,
        numresults=count,
        totalHosts=totalHosts,
        page=page,
        hosts=context,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/searchmodal")
@is_authenticated
def search_modal() -> str:
    return render_template("includes/search_modal_content.html")


@bp.route("/screenshots")
@is_authenticated
def screenshots() -> str:
    page = int(request.args.get("page", 1))

    results_per_page, search_offset = results_offset(page)

    total_hosts, total_screenshots, hosts = current_app.elastic.get_current_screenshots(  # type: ignore[attr-defined]
        results_per_page, search_offset
    )

    next_url, prev_url = build_pagination_urls("main.screenshots", page, total_hosts)

    return render_template(
        "main/screenshots.html",
        total_hosts=total_hosts,
        total_screenshots=total_screenshots,
        hosts=hosts,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/status")
@is_authenticated
def status() -> str:
    """
    Simple html representation of the status api
    """
    return render_template("main/status.html")
