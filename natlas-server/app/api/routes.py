from flask import current_app, request
import random
import os
import json
import string
import base64
import hashlib
from PIL import Image
from datetime import datetime as dt
from datetime import timezone as tz
import dateutil.parser
from ipaddress import ip_network
from app import db
from app.models import ScopeItem
from app.api import bp
from app.util import isAcceptableTarget, parse_ssl_data
from libnmap.parser import NmapParser
from app.auth.wrappers import isAgentAuthenticated


def get_target_tags(target):
	targetnet = ip_network(target)
	tags = []
	for scope in current_app.ScopeManager.getScope():
		if scope.overlaps(targetnet):
			scopetags = ScopeItem.query.filter_by(target=str(scope)).first().tags.all()
			for tag in scopetags:
				tags.append(tag.name)
	return list(set(tags)) # make it a set for only uniques, then make it a list to serialize to JSON


def get_unique_scan_id():
	scan_id = ''
	while scan_id == '':
		rand = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(16))
		count, context = current_app.elastic.gethost_scan_id(rand)
		if count == 0:
			scan_id = rand
	return scan_id


def prepare_work(work):
	work['tags'] = get_target_tags(work['target'])
	work['type'] = 'nmap'
	work['agent_config'] = current_app.agentConfig
	work['agent_config']['scripts'] = current_app.agentScriptStr
	work["services_hash"] = current_app.current_services["sha256"]
	work['scan_id'] = get_unique_scan_id()
	work['status'] = 200
	work['message'] = "Target: " + str(work['target'])
	return work


@bp.route('/getwork', methods=['GET'])
@isAgentAuthenticated
def getwork():
	manual = request.args.get('target', '')
	if "natlas-agent" in request.headers["user-agent"]:
		verstr = request.headers["user-agent"].split('/')[1]
		if verstr != current_app.config["NATLAS_VERSION"]:
			errmsg = "The server detected you were running version {} but the server is running {}".format(verstr, current_app.config["NATLAS_VERSION"])
			return json.dumps({'status': 400, 'message': errmsg, 'retry': False}), 400, {'Content-Type': 'application/json'}
	work = {}

	if manual:
		canTarget = isAcceptableTarget(manual)
		if canTarget:
			work['scan_reason'] = 'manual'
			work['target'] = manual
			work = prepare_work(work)
			return json.dumps(work), 200, {'Content-Type': 'application/json'}
		else:
			errmsg = "{} is not a valid target for this server.".format(manual)
			return json.dumps({'status': 400, 'message': errmsg, 'retry': False}), 400, {'Content-Type': 'application/json'}

	rescans = current_app.ScopeManager.getPendingRescans()
	if len(rescans) == 0: # If there aren't any rescans, update the Rescan Queue and get it again, because of lazy loading
		current_app.ScopeManager.updatePendingRescans()
		rescans = current_app.ScopeManager.getPendingRescans()

	if len(rescans) == 0: # if we don't have rescans, use the ScanManager
		scanmanager = current_app.ScopeManager.getScanManager()
		if not scanmanager:
			current_app.ScopeManager.update()
			scanmanager = current_app.ScopeManager.getScanManager()

			if not scanmanager:
				return json.dumps({'status': 404, 'message': 'No scope is currently configured.', "retry": True}), 404, {'Content-Type': 'application/json'}

		work['target'] = str(scanmanager.getNextIP())
		work['scan_reason'] = 'auto'

	else: # Get the ip from the rescan queue, mark the job as dispatched, update the PendingRescans for other requests
		work['target'] = rescans[0].target
		work['scan_reason'] = 'requested'
		rescans[0].dispatchTask()
		db.session.add(rescans[0])
		db.session.commit()
		current_app.ScopeManager.updatePendingRescans()
		current_app.ScopeManager.updateDispatchedRescans()

	work = prepare_work(work)

	return json.dumps(work), 200, {'Content-Type': 'application/json'}


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

		return json.dumps({"status": 200, "message": "Received: " + newhost['ip']}), 200, {'Content-Type': 'application/json'}

	nmap = NmapParser.parse(newhost['xml_data'])

	# Some quick checks to ensure there are hosts in the scan data
	if nmap.hosts_total != 1:
		return json.dumps({"status": 400, "message": "XML had too many hosts in it", 'retry': False}), 400, {'Content-Type': 'application/json'}

	newhost['ip'] = nmap.hosts[0].address
	if not isAcceptableTarget(newhost['ip']):
		return json.dumps({"status": 400, "message": "Out of scope: " + newhost['ip'], 'retry': False}), 400, {'Content-Type': 'application/json'}

	if len(nmap.hosts[0].hostnames) > 0:
		newhost['hostname'] = nmap.hosts[0].hostnames[0]

	newhost['ctime'] = dt.now(tz.utc)
	newhost['is_up'] = nmap.hosts[0].is_up()
	if not newhost['is_up']:
		current_app.elastic.newhost(newhost)
		return json.dumps({"status": 200, "message": "Thanks for telling us " + newhost['ip'] + " is down"}), 200, {'Content-Type': 'application/json'}

	tmpports = []
	newhost['ports'] = []

	for port in nmap.hosts[0].get_open_ports():
		tmpports.append(str(port[0]))
		srv = nmap.hosts[0].get_service(port[0], port[1])
		portinfo = srv.get_dict()
		portinfo['service'] = srv.service_dict
		portinfo['scripts'] = []
		for script in srv.scripts_results:
			scriptsave = {"id": script['id'], "output": script["output"]}
			portinfo['scripts'].append(scriptsave)
			if script['id'] == "ssl-cert":
				portinfo['ssl'] = parse_ssl_data(script)

		newhost['ports'].append(portinfo)

	newhost['port_str'] = ', '.join(tmpports)

	if 'screenshots' in newhost and newhost['screenshots']:

		# Handle screenshots
		thumb_size = (255, 160)
		num_screenshots = 0
		for item in newhost['screenshots']:
			if item['service'] == 'VNC':
				file_ext = '.jpg'
			else: # Handles http, https files from aquatone/chromium-headless
				file_ext = '.png'

			image = base64.b64decode(item['data'])
			image_hash = hashlib.sha256(image).hexdigest()

			hashpath = "{}/{}".format(image_hash[0:2], image_hash[2:4])
			dirpath = os.path.join(current_app.config["MEDIA_DIRECTORY"], "original", hashpath)

			# makedirs attempts to make every directory necessary to get to the "thumbs" folder: YYYY/MM/DD/HH/thumbs
			os.makedirs(dirpath, exist_ok=True)

			fname = os.path.join(dirpath, image_hash + file_ext)
			with open(fname, 'wb') as f:
				f.write(image)
			item['hash'] = image_hash
			del item['data']

			thumb = Image.open(fname)
			thumb.thumbnail(thumb_size)
			thumb_hash = hashlib.sha256(thumb.tobytes()).hexdigest()
			thumbhashpath = "{}/{}".format(thumb_hash[0:2], thumb_hash[2:4])
			thumbpath = os.path.join(current_app.config["MEDIA_DIRECTORY"], "thumbs", thumbhashpath)
			os.makedirs(thumbpath, exist_ok=True)
			fname = os.path.join(thumbpath, thumb_hash + file_ext)
			thumb.save(fname)
			thumb.close()
			item['thumb_hash'] = thumb_hash
			num_screenshots += 1

		newhost['num_screenshots'] = num_screenshots

	if len(newhost['ports']) == 0:
		return json.dumps({"status": 200, "message": "Expected open ports but didn't find any for %s" % newhost['ip']}), 200, {"Content-Type": "application/json"}

	if len(newhost['ports']) > 500:
		return json.dumps({"status": 200, "message": "More than 500 ports found, throwing data out"}), 200, {"Content-Type": "application/json"}

	current_app.elastic.newhost(newhost)

	return json.dumps({"status": 200, "message": "Received %s ports for %s" % (len(newhost['ports']), newhost['ip'])}), 200, {"Content-Type": "application/json"}


@bp.route('/natlas-services', methods=['GET'])
@isAgentAuthenticated
def natlasServices():
	if current_app.current_services["id"] != "None":
		tmpdict = current_app.current_services.copy() # make an actual copy of the dict so that we can remove the list
		del tmpdict['as_list'] # don't return the "as_list" version of the services, which is only used for making a pretty table.
		return json.dumps(tmpdict), 200, {'Content-Type': 'application/json'}
	return json.dumps(current_app.current_services), 404, {'Content-Type': 'application/json'}
