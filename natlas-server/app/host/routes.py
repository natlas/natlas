from datetime import datetime

import werkzeug
from flask import (
    Response,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app import db, scope_manager
from app.admin.forms import DeleteForm
from app.auth.wrappers import is_authenticated
from app.host import bp
from app.host.forms import RescanForm
from app.host.migrators import determine_data_version
from app.host.summarizers import hostinfo
from app.models import RescanTask


@bp.route("/<ip:ip>")
@is_authenticated
def host(ip: str) -> str:
    info, context = hostinfo(ip)
    delForm = DeleteForm()
    delHostForm = DeleteForm()
    rescanForm = RescanForm()

    version = determine_data_version(context)
    template_str = f"host/versions/{version}/summary.html"
    return render_template(
        template_str,
        **context,
        host=context,
        info=info,
        delForm=delForm,
        delHostForm=delHostForm,
        rescanForm=rescanForm,
    )


@bp.route("/<ip:ip>/history")
@is_authenticated
def host_history(ip: str) -> str:
    info, context = hostinfo(ip)
    page = int(request.args.get("p", 1))
    searchOffset = current_user.results_per_page * (page - 1)

    delHostForm = DeleteForm()
    rescanForm = RescanForm()

    count, context = current_app.elastic.get_host_history(  # type: ignore[attr-defined]
        ip, current_user.results_per_page, searchOffset
    )
    if count == 0:
        return abort(404)
    next_url = (
        url_for("host.host_history", ip=ip, p=page + 1)
        if count > page * current_user.results_per_page
        else None
    )
    prev_url = url_for("host.host_history", ip=ip, p=page - 1) if page > 1 else None

    # TODO Hardcoding the version here is bad. Revisit this.
    return render_template(
        "host/versions/0.6.5/history.html",
        ip=ip,
        info=info,
        page=page,
        numresults=count,
        hosts=context,
        next_url=next_url,
        prev_url=prev_url,
        delHostForm=delHostForm,
        rescanForm=rescanForm,
    )


@bp.route("/<ip:ip>/<scan_id>")
@is_authenticated
def host_historical_result(ip: str, scan_id: str) -> str:
    delForm = DeleteForm()
    delHostForm = DeleteForm()
    rescanForm = RescanForm()
    info, context = hostinfo(ip)
    count, context = current_app.elastic.get_host_by_scan_id(scan_id)  # type: ignore[attr-defined]

    version = determine_data_version(context)
    template_str = f"host/versions/{version}/summary.html"
    return render_template(
        template_str,
        host=context,
        info=info,
        **context,
        delForm=delForm,
        delHostForm=delHostForm,
        rescanForm=rescanForm,
    )


@bp.route("/<ip:ip>/<scan_id>.<ext>")
@is_authenticated
def export_scan(ip: str, scan_id: str, ext: str) -> Response:
    if ext not in ["xml", "nmap", "gnmap", "json"]:
        abort(404)

    export_field = f"{ext}_data"

    mime = "application/json" if ext == "json" else "text/plain"
    count, context = current_app.elastic.get_host_by_scan_id(scan_id)  # type: ignore[attr-defined]
    if ext == "json" and count > 0:
        return jsonify(context)
    if count > 0 and export_field in context:
        return Response(context[export_field], mimetype=mime)
    abort(404)
    # This return is unreachable but the RET503 linter doesn't understand that abort is a NoReturn apparently?
    return None  # type: ignore[unreachable]


@bp.route("/<ip:ip>/screenshots")
@is_authenticated
def host_screenshots(ip: str) -> str:
    page = int(request.args.get("p", 1))
    searchOffset = current_user.results_per_page * (page - 1)

    delHostForm = DeleteForm()
    rescanForm = RescanForm()
    info, context = hostinfo(ip)
    total_entries, screenshots = current_app.elastic.get_host_screenshots(  # type: ignore[attr-defined]
        ip, current_user.results_per_page, searchOffset
    )

    next_url = (
        url_for("host.host_screenshots", ip=ip, p=page + 1)
        if total_entries > page * current_user.results_per_page
        else None
    )
    prev_url = url_for("host.host_screenshots", ip=ip, p=page - 1) if page > 1 else None

    version = determine_data_version(context)
    template_str = f"host/versions/{version}/screenshots.html"
    return render_template(
        template_str,
        **context,
        historical_screenshots=screenshots,
        numresults=total_entries,
        info=info,
        delHostForm=delHostForm,
        rescanForm=rescanForm,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/<ip:ip>/rescan", methods=["POST"])
@login_required  # type: ignore[misc]
def rescan_host(ip: str) -> werkzeug.wrappers.response.Response:
    rescanForm = RescanForm()

    if not (rescanForm.validate_on_submit() or scope_manager.is_acceptable_target(ip)):
        flash(f"Could not handle rescan request for {ip}", "danger")
        return redirect(url_for("host.host", ip=ip))

    incompleteScans = scope_manager.get_incomplete_scans()
    scan_dispatched = {}
    for scan in incompleteScans:
        scan_dispatched[scan.target] = scan

    if ip in scan_dispatched:
        scan = scan_dispatched[ip]
        scan_window = current_app.agentConfig["scanTimeout"] * 2  # type: ignore[attr-defined]
        if (
            scan.dispatched
            and (datetime.utcnow() - scan.date_dispatched).seconds > scan_window  # type: ignore[operator]
        ):
            # It should never take this long so mark it as not dispatched
            scan.dispatched = False
            db.session.commit()
            scope_manager.update_pending_rescans()
            scope_manager.update_dispatched_rescans()
            flash(f"Refreshed stale rescan request for {ip}", "success")
            return redirect(url_for("host.host", ip=ip))
        flash(f"There's an outstanding rescan request for {ip}", "warning")
        return redirect(url_for("host.host", ip=ip))

    rescan = RescanTask(user_id=current_user.id, target=ip)
    db.session.add(rescan)
    db.session.commit()
    scope_manager.update_pending_rescans()
    scope_manager.update_dispatched_rescans()
    flash(f"Requested rescan of {ip}", "success")
    return redirect(url_for("host.host", ip=ip))


@bp.route("/random")
@is_authenticated
def random_host() -> str:
    random_host = current_app.elastic.random_host()  # type: ignore[attr-defined]
    # This would most likely occur when there are no hosts up in the index, so just throw a 404
    if not random_host:
        return abort(404)
    ip = random_host["ip"]
    info, context = hostinfo(ip)
    delForm = DeleteForm()
    delHostForm = DeleteForm()
    rescanForm = RescanForm()

    version = determine_data_version(context)
    template_str = f"host/versions/{version}/summary.html"
    return render_template(
        template_str,
        **context,
        host=context,
        info=info,
        delForm=delForm,
        delHostForm=delHostForm,
        rescanForm=rescanForm,
    )
