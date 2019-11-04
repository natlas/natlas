from flask import redirect, url_for, render_template, \
	Response, current_app, request, send_from_directory
from flask_login import current_user
from app.main import bp
from app.auth.wrappers import isAuthenticated


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
	query = request.args.get('query', '')
	page = int(request.args.get('page', 1))
	format = request.args.get('format', '')
	scan_ids = request.args.get('includeScanIDs', '')
	includeHistory = request.args.get('includeHistory', False)

	results_per_page = current_user.results_per_page
	if includeHistory:
		searchIndex = "nmap_history"
	else:
		searchIndex = "nmap"

	searchOffset = results_per_page * (page - 1)
	count, context = current_app.elastic.search(query, results_per_page, searchOffset, searchIndex=searchIndex)
	totalHosts = current_app.elastic.totalHosts()

	if includeHistory:
		next_url = url_for('main.search', query=query, page=page + 1, includeHistory=includeHistory) \
			if count > page * results_per_page else None
		prev_url = url_for('main.search', query=query, page=page - 1, includeHistory=includeHistory) \
			if page > 1 else None
	else:
		next_url = url_for('main.search', query=query, page=page + 1) \
			if count > page * results_per_page else None
		prev_url = url_for('main.search', query=query, page=page - 1) \
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


@bp.route("/screenshots")
@bp.route("/screenshots/")
def browseScreenshots():
	page = int(request.args.get('p', 1))
	searchOffset = current_user.results_per_page * (page - 1)

	total_hosts, total_screenshots, hosts = current_app.elastic.get_current_screenshots(current_user.results_per_page, searchOffset)

	next_url = url_for('main.browseScreenshots', p=page + 1) \
		if total_hosts > page * current_user.results_per_page else None
	prev_url = url_for('main.browseScreenshots', p=page - 1) \
		if page > 1 else None

	return render_template("screenshots.html", numresults=total_screenshots, hosts=hosts, next_url=next_url, prev_url=prev_url)
