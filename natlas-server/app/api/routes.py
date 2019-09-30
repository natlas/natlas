from flask import current_app, request, jsonify
import random, os, json, ipaddress, string

from datetime import datetime as dt
from datetime import timezone as tz
import dateutil.parser
from ipaddress import ip_network

from app import db
from app.models import NatlasServices, ScopeItem, Tag
from app.api import bp
from app.util import isAcceptableTarget
from libnmap.parser import NmapParser
from app.auth.wrappers import isAgentAuthenticated

@bp.route('/getwork', methods=['GET'])
@isAgentAuthenticated
def getwork():
	if "natlas-agent" in request.headers["user-agent"]:
		verstr = request.headers["user-agent"].split('/')[1]
		if verstr != current_app.config["NATLAS_VERSION"]:
			errmsg = "The server detected you were running version {} but the server is running {}".format(verstr, current_app.config["NATLAS_VERSION"])
			return json.dumps({'status': 400, 'message': errmsg, 'retry':False}), 400, {'content-type':'application/json'}
	work = {}
	rescans = current_app.ScopeManager.getPendingRescans()
	if len(rescans) == 0: # If there aren't any rescans, update the Rescan Queue and get it again, because of lazy loading
		current_app.ScopeManager.updatePendingRescans()
		rescans = current_app.ScopeManager.getPendingRescans()

	if len(rescans) == 0: # if we don't have rescans, use the ScanManager
		scanmanager = current_app.ScopeManager.getScanManager()
		if scanmanager == None:
			current_app.ScopeManager.update()
			scanmanager = current_app.ScopeManager.getScanManager()

			if scanmanager == None:
				return json.dumps({ 'status': 404, 'message': 'No scope is currently configured.', "retry": True }), 404, {'content-type':'application/json'}

		ip = scanmanager.getNextIP()
		work['scan_reason'] = 'auto'

	else: # Get the ip from the rescan queue, mark the job as dispatched, update the PendingRescans for other requests
		ip = rescans[0].target
		work['scan_reason'] = 'requested'
		rescans[0].dispatchTask()
		db.session.add(rescans[0])
		db.session.commit()
		current_app.ScopeManager.updatePendingRescans()
		current_app.ScopeManager.updateDispatchedRescans()

	targetnet = ip_network(ip)
	tags = []
	for scope in current_app.ScopeManager.getScope():
		if scope.overlaps(targetnet):
			scopetags = ScopeItem.query.filter_by(target=str(scope)).first().tags.all()
			for tag in scopetags:
				tags.append(tag.name)
	work['tags'] = tags


	work['type'] = 'nmap'
	work['agent_config'] = current_app.agentConfig
	work['agent_config']['scripts'] = current_app.agentScriptStr
	work["services_hash"] = current_app.current_services["sha256"]
	scan_id = ''
	while scan_id == '':
		rand = ''.join(random.choice(string.ascii_lowercase + string.digits)
			   for _ in range(16))
		count, context = current_app.elastic.gethost_scan_id(rand)
		if count == 0:
			scan_id = rand
	work['scan_id'] = scan_id
	work['target'] = str(ip)
	work['status'] = 200
	work['message'] = "Target: " + str(ip)

	return json.dumps(work), 200, {'content-type':'application/json'}


@bp.route('/submit', methods=['POST'])
@isAgentAuthenticated
def submit():
	data = request.get_json()
	newhost = {}
	newhost = json.loads(data)
	if newhost['scan_reason'] != 'auto':
		dispatched = current_app.ScopeManager.getDispatchedRescans()
		for scan in dispatched:
			if scan.target == newhost['ip']:
				scan.completeTask(newhost['scan_id'])
				db.session.add(scan)
				db.session.commit()
				current_app.ScopeManager.updateDispatchedRescans()
				break

	if newhost['scan_start'] and newhost['scan_stop']:
		elapsed = dateutil.parser.parse(newhost['scan_stop']) - dateutil.parser.parse(newhost['scan_start'])
		newhost['elapsed'] = elapsed.seconds
	# If the agent data has an is_up and it's false, store that in the database
	if not newhost["is_up"] or (newhost["is_up"] and newhost["port_count"] == 0):
		newhost["ctime"] = dt.now(tz.utc)
		current_app.elastic.newhost(newhost)

		return json.dumps({"status":200, "message": "Received: " + newhost['ip']}), 200, {'content-type':'application/json'}

	nmap = NmapParser.parse(newhost['xml_data'])

	# Some quick checks to ensure there are hosts in the scan data
	if nmap.hosts_total != 1:
		return json.dumps({"status":400, "message":"XML had too many hosts in it", 'retry':False}), 400, {'content-type':'application/json'}

	newhost['ip'] = nmap.hosts[0].address
	if not isAcceptableTarget(newhost['ip']):
		return json.dumps({"status":400, "message":"Out of scope: " + newhost['ip'], 'retry':False}), 400, {'content-type':'application/json'}

	if len(nmap.hosts[0].hostnames) > 0:
		newhost['hostname'] = nmap.hosts[0].hostnames[0]

	newhost['ctime'] = dt.now(tz.utc)
	newhost['is_up'] = nmap.hosts[0].is_up()
	if not newhost['is_up']:
		current_app.elastic.newhost(newhost)
		return json.dumps({"status":200, "message":"Thanks for telling us " + newhost['ip'] +" is down"}), 200, {'content-type':'application/json'}

	tmpports = []
	newhost['ports'] = []

	for port in nmap.hosts[0].get_ports():
		tmpports.append(str(port[0]))
		srv = nmap.hosts[0].get_service(port[0])
		portinfo = srv.get_dict()
		portinfo['service'] = srv.service_dict
		portinfo['scripts'] = []
		for script in srv.scripts_results:
			scriptsave = {"id": script['id'], "output": script["output"]}
			portinfo['scripts'].append(scriptsave)


		newhost['ports'].append(portinfo)

	newhost['port_str'] = ', '.join(tmpports)

	if len(newhost['ports']) == 0:
		return json.dumps({"status":200, "message":"Expected open ports but didn't find any for %s" % newhost['ip']}), 200, {"content-type":"application/json"}

	if len(newhost['ports']) > 500:
		return json.dumps({"status":200, "message":"More than 500 ports found, throwing data out"}), 200, {"content-type":"application/json"}

	current_app.elastic.newhost(newhost)

	return json.dumps({"status":200, "message":"Received %s ports for %s" % (len(newhost['ports']), newhost['ip'])}), 200, {"content-type":"application/json"}

@bp.route('/natlas-services', methods=['GET'])
@isAgentAuthenticated
def natlasServices():
	if current_app.current_services["id"] != "None":
		tmpdict = current_app.current_services.copy() # make an actual copy of the dict so that we can remove the list
		del tmpdict['as_list'] # don't return the "as_list" version of the services, which is only used for making a pretty table.
		return json.dumps(tmpdict), 200, {'content-type':'application/json'}
	return json.dumps(current_app.current_services), 404, {'content-type':'application/json'}
