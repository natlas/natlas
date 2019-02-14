from flask import current_app, request
import random, os, json, ipaddress, string

from datetime import datetime

from app.models import NatlasServices
from app.api import bp
from app.util import isAcceptableTarget
from app.nmap_parser import NmapParser

@bp.route('/getwork', methods=['GET'])
def getwork():
    scanmanager = current_app.ScopeManager.getScanManager()
    if scanmanager == None:
            return json.dumps({ 'errorcode': 404, 'message': 'No scope is currently configured.' }), 404, {'content-type':'application/json'}

    ip = scanmanager.getNextIP()

    work = {}
    work['type'] = 'nmap'
    work['agent_config'] = current_app.agentConfig
    work["services_hash"] = current_app.current_services["sha256"]
    scan_id = ''
    while scan_id == '':
        rand = ''.join(random.choice(string.ascii_lowercase + string.digits)
               for _ in range(10))
        count, context = current_app.elastic.gethost_scan_id(rand)
        if count == 0:
            scan_id = rand
    work['scan_id'] = scan_id
    work['target'] = str(ip)

    return json.dumps(work), 200, {'content-type':'application/json'}


@bp.route('/submit', methods=['POST'])
def submit():
    nmap = NmapParser()
    data = request.get_json()

    newhost = {}
    newhost = json.loads(data)

    if not nmap.has_scan_report(newhost['nmap_data']):
        return "[!] No scan report found! Make sure your scan includes \"%s\"" % nmap.REPORT

    try:
        newhost['ip'] = nmap.get_ip(newhost['nmap_data'])
        if not isAcceptableTarget(newhost['ip']):
            return "[!] This address isn't in our authorized scope!"
        newhost['hostname'] = nmap.get_hostname(newhost['nmap_data'])
        newhost['ports'] = str(nmap.get_ports(newhost['nmap_data']))
        newhost['ctime'] = datetime.now()
    except Exception as e:
        return "[!] Couldn't find necessary nmap_data\n" + str(e)

    if len(newhost['ports']) == 0:
        return "[!] No open ports found!"

    if len(newhost['ports']) > 500:
        return "[!] More than 500 ports found. This is probably an IDS/IPS. We're going to throw the data out."

    current_app.elastic.newhost(newhost)

    return "[+] nmap successful and submitted for ip: "+newhost['ip']

@bp.route('/natlas-services', methods=['GET'])
def natlasServices():
    if current_app.current_services["id"] != "None":
        return json.dumps(current_app.current_services), 200, {'content-type':'application/json'}
    return json.dumps(current_app.current_services), 404, {'content-type':'application/json'}
