from flask import (
    current_app,
    render_template,
    url_for,
    Response,
    request,
    flash,
    abort,
    redirect,
    jsonify,
)
from flask_login import current_user, login_required
from datetime import datetime
from app.models import RescanTask
from app.admin.forms import DeleteForm
from app.host.forms import RescanForm
from app.host.summarizers import hostinfo
from app.host.migrators import determine_data_version
from app.host import bp
from app.auth.wrappers import is_authenticated
from app import db


@bp.route("/<ip>")
@bp.route("/<ip>/")
@is_authenticated
def host(ip):
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


@bp.route("/<ip>/history")
@bp.route("/<ip>/history/")
@is_authenticated
def host_history(ip):
    info, context = hostinfo(ip)
    page = int(request.args.get("p", 1))
    searchOffset = current_user.results_per_page * (page - 1)

    delHostForm = DeleteForm()
    rescanForm = RescanForm()

    count, context = current_app.elastic.get_host_history(
        ip, current_user.results_per_page, searchOffset
    )
    if count == 0:
        abort(404)
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


@bp.route("/<ip>/<scan_id>")
@is_authenticated
def host_historical_result(ip, scan_id):
    delForm = DeleteForm()
    delHostForm = DeleteForm()
    rescanForm = RescanForm()
    info, context = hostinfo(ip)
    count, context = current_app.elastic.get_host_by_scan_id(scan_id)

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


@bp.route("/<ip>/<scan_id>.<ext>")
@is_authenticated
def export_scan(ip, scan_id, ext):
    if ext not in ["xml", "nmap", "gnmap", "json"]:
        abort(404)

    export_field = f"{ext}_data"

    mime = "application/json" if ext == "json" else "text/plain"
    count, context = current_app.elastic.get_host_by_scan_id(scan_id)
    if ext == "json" and count > 0:
        return jsonify(context)
    elif count > 0 and export_field in context:
        return Response(context[export_field], mimetype=mime)
    else:
        abort(404)


@bp.route("/<ip>/screenshots")
@bp.route("/<ip>/screenshots/")
@is_authenticated
def host_screenshots(ip):
    page = int(request.args.get("p", 1))
    searchOffset = current_user.results_per_page * (page - 1)

    delHostForm = DeleteForm()
    rescanForm = RescanForm()
    info, context = hostinfo(ip)
    total_entries, screenshots = current_app.elastic.get_host_screenshots(
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


@bp.route("/<ip>/rescan", methods=["POST"])
@login_required
def rescan_host(ip):
    rescanForm = RescanForm()

    if not (
        rescanForm.validate_on_submit()
        or current_app.ScopeManager.is_acceptable_target(ip)
    ):
        flash(f"Could not handle rescan request for {ip}", "danger")
        return redirect(url_for("host.host", ip=ip))

    incompleteScans = current_app.ScopeManager.get_incomplete_scans()
    scan_dispatched = {}
    for scan in incompleteScans:
        scan_dispatched[scan.target] = scan

    if ip in scan_dispatched:
        scan = scan_dispatched[ip]
        scan_window = current_app.agentConfig["scanTimeout"] * 2
        if (
            scan.dispatched
            and (datetime.utcnow() - scan.date_dispatched).seconds > scan_window
        ):
            # It should never take this long so mark it as not dispatched
            scan.dispatched = False
            db.session.commit()
            current_app.ScopeManager.update_pending_rescans()
            current_app.ScopeManager.update_dispatched_rescans()
            flash(f"Refreshed stale rescan request for {ip}", "success")
            return redirect(url_for("host.host", ip=ip))
        flash(f"There's an outstanding rescan request for {ip}", "warning")
        return redirect(url_for("host.host", ip=ip))

    rescan = RescanTask(user_id=current_user.id, target=ip)
    db.session.add(rescan)
    db.session.commit()
    current_app.ScopeManager.update_pending_rescans()
    current_app.ScopeManager.update_dispatched_rescans()
    flash(f"Requested rescan of {ip}", "success")
    return redirect(url_for("host.host", ip=ip))


@bp.route("/random")
@bp.route("/random/")
@is_authenticated
def random_host():
    random_host = current_app.elastic.random_host()
    # This would most likely occur when there are no hosts up in the index, so just throw a 404
    if not random_host:
        abort(404)
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
