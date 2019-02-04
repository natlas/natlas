from flask import redirect, url_for, flash, render_template, Response, current_app, g, request
from app.main import bp
from app.util import hostinfo
from app.auth.wrappers import isAuthenticated, isAdmin

@bp.before_app_request
def before_request():
    g.preview_length = current_app.config['PREVIEW_LENGTH']

@bp.route('/')
@isAuthenticated
def index():
    return redirect(url_for('main.search'))

@bp.route('/search')
@isAuthenticated
def search():
    query = request.args.get('q', '')
    page = int(request.args.get('p', 1))
    format = request.args.get('f', '')
    scan_ids = request.args.get('s', '')

    searchOffset = current_app.config['RESULTS_PER_PAGE'] * (page-1)
    count, context = current_app.elastic.search(
        query, current_app.config['RESULTS_PER_PAGE'], searchOffset)

    next_url = url_for('main.search', q=query, p=page + 1) \
        if count > page * current_app.config['RESULTS_PER_PAGE'] else None
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
        return render_template("search.html", query=query, numresults=count, page=page, hosts=context, next_url=next_url, prev_url=prev_url)

@bp.route('/host/<ip>')
@bp.route('/host/<ip>/')
@isAuthenticated
def host(ip):
    info, context = hostinfo(ip)
    return render_template("host/summary.html", **context, host=context, info=info)


@bp.route('/host/<ip>/history')
@bp.route('/host/<ip>/history/')
@isAuthenticated
def host_history(ip):
    info, context = hostinfo(ip)
    page = int(request.args.get('p', 1))
    searchOffset = current_app.config['RESULTS_PER_PAGE'] * (page-1)

    count, context = current_app.elastic.gethost_history(
        ip, current_app.config['RESULTS_PER_PAGE'], searchOffset)
    if count == 0:
        abort(404)
    next_url = url_for('main.host_history', ip=ip, p=page + 1) \
        if count > page * current_app.config['RESULTS_PER_PAGE'] else None
    prev_url = url_for('main.host_history', ip=ip, p=page - 1) \
        if page > 1 else None

    return render_template("host/history.html", ip=ip, info=info, page=page, hosts=context, next_url=next_url, prev_url=prev_url)

@bp.route('/host/<ip>/<scan_id>')
@isAuthenticated
def host_historical_result(ip, scan_id):

    info, context = hostinfo(ip)
    count, context = current_app.elastic.gethost_scan_id(scan_id)
    return render_template("host/summary.html", host=context, info=info, **context)

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

@bp.route('/host/<ip>/headshots')
@bp.route('/host/<ip>/headshots/')
@isAuthenticated
def host_headshots(ip):

    info, context = hostinfo(ip)
    return render_template("host/headshots.html", **context, info=info)