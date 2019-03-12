from flask import current_app, request
import random, os, json, ipaddress, string

from datetime import datetime as dt
from datetime import timezone as tz
import dateutil.parser

from app.models import NatlasServices
from app.api import bp
from app.util import isAcceptableTarget
from libnmap.parser import NmapParser

@bp.route('/getwork', methods=['GET'])
def getwork():
    scanmanager = current_app.ScopeManager.getScanManager()
    if scanmanager == None:
        current_app.ScopeManager.update()
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
    
    data = request.get_json()
    
    newhost = {}
    newhost = json.loads(data)
    if newhost['scan_start'] and newhost['scan_stop']:
        elapsed = dateutil.parser.parse(newhost['scan_stop']) - dateutil.parser.parse(newhost['scan_start'])
        newhost['elapsed'] = elapsed.seconds
    # If the agent data has an is_up and it's false, store that in the database
    if not newhost["is_up"] or (newhost["is_up"] and newhost["port_count"] == 0):
        newhost["ctime"] = dt.now(tz.utc)
        current_app.elastic.newhost(newhost)
        return "[+] We've received your report for: " + newhost['ip']

    nmap = NmapParser.parse(newhost['xml_data'])
    
    # Some quick checks to ensure there are hosts in the scan data
    if nmap.hosts_total != 1:
        return "[!] We require exactly one host in scan results right now"

    newhost['ip'] = nmap.hosts[0].address
    if not isAcceptableTarget(newhost['ip']):
        return "[!] This address isn't in our authorized scope!"

    if len(nmap.hosts[0].hostnames) > 0:
        newhost['hostname'] = nmap.hosts[0].hostnames[0]
    else:
        newhost['hostname'] = ''

    newhost['ctime'] = dt.now(tz.utc)
    newhost['is_up'] = nmap.hosts[0].is_up()
    if not newhost['is_up']:
        current_app.elastic.newhost(newhost)
        return "[+] Thanks for telling us that this host is down" + newhost['ip']

    tmpports = []
    newhost['structured_ports'] = {'tcp': {}, 'udp': {}}
    idx = 0
    for port in nmap.hosts[0].get_ports():
        tmpports.append(str(port[0]))
        nmapservice = nmap.hosts[0].get_service(port[0])
        newhost['structured_ports'][port[1]][idx] = nmapservice.get_dict()
        idx += 1
    
    newhost['ports'] = ', '.join(tmpports) 

    if len(newhost['structured_ports']['tcp']) == 0 and len(newhost['structured_ports']['udp']) == 0:
        return "[!] No open ports found!"

    if len(newhost['structured_ports']['tcp']) + len(newhost['structured_ports']['udp']) > 500:
        return "[!] More than 500 ports found. This is probably an IDS/IPS. We're going to throw the data out."

    current_app.elastic.newhost(newhost)

    return "[+] nmap successful and submitted for ip: "+newhost['ip']

@bp.route('/natlas-services', methods=['GET'])
def natlasServices():
    if current_app.current_services["id"] != "None":
        return json.dumps(current_app.current_services), 200, {'content-type':'application/json'}
    return json.dumps(current_app.current_services), 404, {'content-type':'application/json'}
