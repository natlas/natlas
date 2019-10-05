from flask import redirect, url_for, flash, render_template, \
				Response, current_app, g, request, send_from_directory

from flask_login import current_user, login_required
from app.main import bp
from app.util import hostinfo, isAcceptableTarget
from app.auth.wrappers import isAuthenticated, isAdmin
from app.admin.forms import DeleteForm
from app.main.forms import RescanForm
from app.models import RescanTask
from app import db
import json
from datetime import datetime, timedelta
import random

@bp.route('/')
@isAuthenticated
def index():
	return redirect(url_for('main.search'))

# Serve media files in case the front-end proxy doesn't do it
@bp.route('/media/<path:filename>')
def send_media(filename):
	# If you're looking at this function, wondering why your files aren't sending...
	# It's probably because current_app.config['MEDIA_DIRECTORY'] isn't pointing to an absolute file path
	return send_from_directory(current_app.config['MEDIA_DIRECTORY'], filename)

@bp.route('/search')
@isAuthenticated
def search():
	query = request.args.get('q', '')
	page = int(request.args.get('p', 1))
	format = request.args.get('f', '')
	scan_ids = request.args.get('s', '')


	searchOffset = current_user.results_per_page * (page-1)
	count, context = current_app.elastic.search(query, current_user.results_per_page, searchOffset)
	totalHosts = current_app.elastic.totalHosts()

	next_url = url_for('main.search', q=query, p=page+1) \
		 if count > page * current_user.results_per_page else None
	prev_url = url_for('main.search', q=query, p=page - 1) \
		if page > 1 else None

	# what kind of output are we looking for?
	if format == 'hostlist':
		hostlist = []
		for host in context:
			if scan_ids:
				hostlist.append(str(host['ip']) + ',' + str(host['scan_id']))
			else:
				hostlist.append(str(host['ip']))
		return Response('\n'.join(hostlist), mimetype='text/plain')
	else:
		return render_template("search.html", query=query, numresults=count, totalHosts=totalHosts, page=page, hosts=context, next_url=next_url, prev_url=prev_url)

@bp.route('/searchmodal')
@isAuthenticated
def search_modal():
	return render_template("includes/search_modal_content.html")

@bp.route('/host/<ip>')
@bp.route('/host/<ip>/')
@isAuthenticated
def host(ip):
	info, context = hostinfo(ip)
	delForm = DeleteForm()
	delHostForm = DeleteForm()
	rescanForm = RescanForm()
	return render_template("host/summary.html", **context, host=context, info=info, delForm=delForm, delHostForm=delHostForm, \
		rescanForm=rescanForm)


@bp.route('/host/<ip>/history')
@bp.route('/host/<ip>/history/')
@isAuthenticated
def host_history(ip):
	info, context = hostinfo(ip)
	page = int(request.args.get('p', 1))
	searchOffset = current_user.results_per_page * (page-1)

	delHostForm = DeleteForm()
	rescanForm = RescanForm()

	count, context = current_app.elastic.gethost_history(
		ip, current_user.results_per_page, searchOffset)
	if count == 0:
		abort(404)
	next_url = url_for('main.host_history', ip=ip, p=page + 1) \
		if count > page * current_user.results_per_page else None
	prev_url = url_for('main.host_history', ip=ip, p=page - 1) \
		if page > 1 else None

	return render_template("host/history.html", ip=ip, info=info, page=page, numresults=count, hosts=context, next_url=next_url, prev_url=prev_url, \
		delHostForm=delHostForm, rescanForm=rescanForm)

@bp.route('/host/<ip>/<scan_id>')
@isAuthenticated
def host_historical_result(ip, scan_id):
	delForm = DeleteForm()
	delHostForm = DeleteForm()
	rescanForm = RescanForm()
	info, context = hostinfo(ip)
	count, context = current_app.elastic.gethost_scan_id(scan_id)
	return render_template("host/summary.html", host=context, info=info, **context, delForm=delForm, delHostForm=delHostForm, rescanForm=rescanForm)

@bp.route('/host/<ip>/<scan_id>.xml')
@isAuthenticated
def export_scan_xml(ip, scan_id):
	count, context = current_app.elastic.gethost_scan_id(scan_id)
	return Response(context['xml_data'], mimetype="text/plain")

@bp.route('/host/<ip>/<scan_id>.nmap')
@isAuthenticated
def export_scan_nmap(ip, scan_id):
	count, context = current_app.elastic.gethost_scan_id(scan_id)
	return Response(context['nmap_data'], mimetype="text/plain")

@bp.route('/host/<ip>/<scan_id>.gnmap')
@isAuthenticated
def export_scan_gnmap(ip, scan_id):
	count, context = current_app.elastic.gethost_scan_id(scan_id)
	return Response(context['gnmap_data'], mimetype="text/plain")

@bp.route('/host/<ip>/<scan_id>.json')
@isAuthenticated
def export_scan_json(ip, scan_id):
	count, context = current_app.elastic.gethost_scan_id(scan_id)
	return Response(json.dumps(context), mimetype="application/json")

@bp.route('/host/<ip>/screenshots')
@bp.route('/host/<ip>/screenshots/')
@isAuthenticated
def host_screenshots(ip):
	page = int(request.args.get('p', 1))
	searchOffset = current_user.results_per_page * (page-1)

	delHostForm = DeleteForm()
	rescanForm = RescanForm()
	info, context = hostinfo(ip)
	total_entries, screenshots = current_app.elastic.get_host_screenshots(ip, current_user.results_per_page, searchOffset)

	next_url = url_for('main.host_screenshots', ip=ip, p=page + 1) \
		if total_entries > page * current_user.results_per_page else None
	prev_url = url_for('main.host_screenshots', ip=ip, p=page - 1) \
		if page > 1 else None

	return render_template("host/screenshots.html", **context, historical_screenshots=screenshots, numresults=total_entries, \
		info=info, delHostForm=delHostForm, rescanForm=rescanForm, next_url=next_url, prev_url=prev_url)

@bp.route('/host/<ip>/rescan', methods=['POST'])
# login_required ensures that an actual user is logged in to make the request
# opposed to isAuthenticated checking site config to see if login is required first
@login_required
def rescan_host(ip):
	rescanForm = RescanForm()

	if rescanForm.validate_on_submit():
		if not isAcceptableTarget(ip):
			# Someone is requesting we scan an ip that isn't allowed
			flash("We're not allowed to scan %s" % ip, "danger")
			return redirect(request.referrer)

		incompleteScans = current_app.ScopeManager.getIncompleteScans()

		for scan in incompleteScans:
			if ip == scan.target:
				if scan.dispatched == True:
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
def randomHost():
	randomHost = current_app.elastic.random_host()
	if not randomHost:
		abort(404)
	ip = randomHost['hits']['hits'][0]['_source']['ip']
	info, context = hostinfo(ip)
	delForm = DeleteForm()
	delHostForm = DeleteForm()
	rescanForm = RescanForm()
	return render_template("host/summary.html", **context, host=context, info=info, delForm=delForm, delHostForm=delHostForm, \
		rescanForm=rescanForm)