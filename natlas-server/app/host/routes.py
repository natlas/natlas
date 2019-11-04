from flask import current_app, render_template, url_for, Response, request, flash, abort, redirect
from flask_login import current_user, login_required
import json
from datetime import datetime
from app.models import RescanTask
from app.admin.forms import DeleteForm
from app.host.forms import RescanForm
from app.host.summarizers import hostinfo
from app.host.migrators import determine_data_version
from app.host import bp
from app.auth.wrappers import isAuthenticated
from app import db


@bp.route('/<ip>')
@bp.route('/<ip>/')
@isAuthenticated
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
		rescanForm=rescanForm
	)


@bp.route('/<ip>/history')
@bp.route('/<ip>/history/')
@isAuthenticated
def host_history(ip):
	info, context = hostinfo(ip)
	page = int(request.args.get('p', 1))
	searchOffset = current_user.results_per_page * (page - 1)

	delHostForm = DeleteForm()
	rescanForm = RescanForm()

	count, context = current_app.elastic.gethost_history(
		ip, current_user.results_per_page, searchOffset)
	if count == 0:
		abort(404)
	next_url = url_for('host.host_history', ip=ip, p=page + 1) \
		if count > page * current_user.results_per_page else None
	prev_url = url_for('host.host_history', ip=ip, p=page - 1) \
		if page > 1 else None

	# TODO Hardcoding the version here is bad. Revisit this.
	return render_template(
		"host/versions/0.6.5/history.html",
		ip=ip, info=info,
		page=page,
		numresults=count,
		hosts=context,
		next_url=next_url,
		prev_url=prev_url,
		delHostForm=delHostForm,
		rescanForm=rescanForm
	)


@bp.route('/<ip>/<scan_id>')
@isAuthenticated
def host_historical_result(ip, scan_id):
	delForm = DeleteForm()
	delHostForm = DeleteForm()
	rescanForm = RescanForm()
	info, context = hostinfo(ip)
	count, context = current_app.elastic.gethost_scan_id(scan_id)

	version = determine_data_version(context)
	template_str = f"host/versions/{version}/summary.html"
	return render_template(
		template_str,
		host=context,
		info=info,
		**context,
		delForm=delForm,
		delHostForm=delHostForm,
		rescanForm=rescanForm
	)


@bp.route('/<ip>/<scan_id>.<ext>')
@isAuthenticated
def export_scan(ip, scan_id, ext):
	if ext not in ['xml', 'nmap', 'gnmap', 'json']:
		abort(404)

	export_field = f"{ext}_data"

	if ext == 'json':
		mime = "application/json"
	else:
		mime = "text/plain"

	count, context = current_app.elastic.gethost_scan_id(scan_id)
	if ext == 'json' and count > 0:
		return Response(json.dumps(context), mimetype=mime)
	elif count > 0 and export_field in context:
		return Response(context[export_field], mimetype=mime)
	else:
		abort(404)


@bp.route('/<ip>/screenshots')
@bp.route('/<ip>/screenshots/')
@isAuthenticated
def host_screenshots(ip):
	page = int(request.args.get('p', 1))
	searchOffset = current_user.results_per_page * (page - 1)

	delHostForm = DeleteForm()
	rescanForm = RescanForm()
	info, context = hostinfo(ip)
	total_entries, screenshots = current_app.elastic.get_host_screenshots(ip, current_user.results_per_page, searchOffset)

	next_url = url_for('host.host_screenshots', ip=ip, p=page + 1) \
		if total_entries > page * current_user.results_per_page else None
	prev_url = url_for('host.host_screenshots', ip=ip, p=page - 1) \
		if page > 1 else None

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
		prev_url=prev_url
	)


@bp.route('/<ip>/rescan', methods=['POST'])
# login_required ensures that an actual user is logged in to make the request
# opposed to isAuthenticated checking site config to see if login is required first
@login_required
def rescan_host(ip):
	rescanForm = RescanForm()

	if rescanForm.validate_on_submit():
		if not current_app.ScopeManager.isAcceptableTarget(ip):
			# Someone is requesting we scan an ip that isn't allowed
			flash("We're not allowed to scan %s" % ip, "danger")
			return redirect(request.referrer)

		incompleteScans = current_app.ScopeManager.getIncompleteScans()

		for scan in incompleteScans:
			if ip == scan.target:
				if scan.dispatched:
					status = "dispatched"
					if (datetime.utcnow() - scan.date_dispatched).seconds > 1200:
						# 20 minutes have past since dispatch, something probably wen't seriously wrong
						# move it back to not dispatched and update the cached rescan data
						scan.dispatched = False
						db.session.add(scan)
						db.session.commit()
						current_app.ScopeManager.updatePendingRescans()
						current_app.ScopeManager.updateDispatchedRescans()
						flash("Refreshed existing rescan request for %s" % ip, "success")
						return redirect(request.referrer)
				else:
					status = "pending"
				flash("There's already a %s rescan request for %s" % (status, ip), "warning")
				return redirect(request.referrer)

		rescan = RescanTask(user_id=current_user.id, target=ip)
		db.session.add(rescan)
		db.session.commit()
		flash("Requested rescan of %s" % ip, "success")
		current_app.ScopeManager.updatePendingRescans()
		current_app.ScopeManager.updateDispatchedRescans()
		return redirect(request.referrer)


@bp.route("/random")
@bp.route("/random/")
def random_host():
	random_host = current_app.elastic.random_host()
	if not random_host:
		abort(404)
	ip = random_host['hits']['hits'][0]['_source']['ip']
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
		rescanForm=rescanForm
	)
