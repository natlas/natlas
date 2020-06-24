from flask import current_app, request, Response, jsonify
import json
from datetime import datetime as dt
from datetime import timezone as tz
import dateutil.parser
from app.api import bp
from app.api.prepare_work import prepare_work
from app.api.processing.screenshot import process_screenshots
from app.api.processing.ssl import parse_ssl_data
from app.api.rescan_handler import mark_scan_dispatched, mark_scan_completed
from libnmap.parser import NmapParser, NmapParserException
from app.auth.wrappers import is_agent_authenticated, is_authenticated
from app.util import pretty_time_delta


json_content = "application/json"


@bp.route("/getwork", methods=["GET"])
@is_agent_authenticated
def getwork():
    manual = request.args.get("target", "")
    if "natlas-agent" in request.headers["user-agent"]:
        verstr = request.headers["user-agent"].split("/")[1]
        if verstr != current_app.config["NATLAS_VERSION"]:
            errmsg = f"The server detected you were running version {verstr} but the server is running {current_app.config['NATLAS_VERSION']}"
            response_body = json.dumps(
                {"status": 400, "message": errmsg, "retry": False}
            )
            response = Response(
                response=response_body, status=400, content_type=json_content
            )
            return response
    work = {}

    if manual:
        canTarget = current_app.ScopeManager.is_acceptable_target(manual)
        if canTarget:
            work["scan_reason"] = "manual"
            work["target"] = manual
            work = prepare_work(work)
            response = Response(
                response=json.dumps(work), status=200, content_type=json_content
            )
        else:
            errmsg = f"{manual} is not a valid target for this server."
            response_body = json.dumps(
                {"status": 400, "message": errmsg, "retry": False}
            )
            response = Response(
                response=response_body, status=400, content_type=json_content
            )
        return response

    rescans = current_app.ScopeManager.get_pending_rescans()
    if (
        len(rescans) == 0
    ):  # If there aren't any rescans, update the Rescan Queue and get it again, because of lazy loading
        current_app.ScopeManager.update_pending_rescans()
        rescans = current_app.ScopeManager.get_pending_rescans()

    if len(rescans) == 0:  # if we don't have rescans, use the ScanManager
        scanmanager = current_app.ScopeManager.get_scan_manager()
        if not scanmanager:
            current_app.ScopeManager.update()
            scanmanager = current_app.ScopeManager.get_scan_manager()

        if not scanmanager:
            response_body = json.dumps(
                {
                    "status": 404,
                    "message": "No scope is currently configured.",
                    "retry": True,
                }
            )
            response = Response(
                response=response_body, status=404, content_type=json_content
            )
            return response

        work["target"] = str(scanmanager.get_next_ip())
        work["scan_reason"] = "auto"

    else:  # Get the ip from the rescan queue, mark the job as dispatched, update the PendingRescans for other requests
        work["target"] = rescans[0].target
        work["scan_reason"] = "requested"
        mark_scan_dispatched(rescans[0])

    work = prepare_work(work)
    response_body = json.dumps(work)
    response = Response(response=response_body, status=200, content_type=json_content)
    return response


@bp.route("/submit", methods=["POST"])
@is_agent_authenticated
def submit():
    status_code = None
    response_body = None
    data = request.get_json()
    newhost = {}
    newhost = json.loads(data)
    newhost["ctime"] = dt.now(tz.utc)
    if newhost["scan_reason"] == "requested":
        mark_scan_completed(newhost["ip"], newhost["scan_id"])

    try:
        nmap = NmapParser.parse(newhost["xml_data"])
        # If there's more or less than 1 host in the xml data, reject it (for now)
        if nmap.hosts_total != 1:
            status_code = 400
            response_body = json.dumps(
                {
                    "status": status_code,
                    "message": "XML had too many hosts in it",
                    "retry": False,
                }
            )

        # If it's not an acceptable target, tell the agent it's out of scope
        elif len(nmap.hosts) == 1 and not current_app.ScopeManager.is_acceptable_target(
            nmap.hosts[0].address
        ):
            status_code = 400
            response_body = json.dumps(
                {
                    "status": status_code,
                    "message": "Out of scope: " + nmap.hosts[0].address,
                    "retry": False,
                }
            )

        # If there's no further processing to do, store the host and prepare the response
        elif not newhost["is_up"] or (newhost["is_up"] and newhost["port_count"] == 0):
            current_app.elastic.new_result(newhost)
            status_code = 200
            response_body = json.dumps(
                {"status": status_code, "message": "Received: " + newhost["ip"]}
            )
    except NmapParserException:
        status_code = 400
        response_body = json.dumps(
            {
                "status": status_code,
                "message": "Invalid nmap xml data provided",
                "retry": False,
            }
        )

    # If status_code and response_body have been set by this point, return a response.
    if status_code and response_body:
        response = Response(
            response=response_body, status=status_code, content_type=json_content
        )
        return response

    if newhost["scan_start"] and newhost["scan_stop"]:
        elapsed = dateutil.parser.parse(newhost["scan_stop"]) - dateutil.parser.parse(
            newhost["scan_start"]
        )
        newhost["elapsed"] = elapsed.seconds

    newhost["ip"] = nmap.hosts[0].address
    if len(nmap.hosts[0].hostnames) > 0:
        newhost["hostname"] = nmap.hosts[0].hostnames[0]

    tmpports = []
    newhost["ports"] = []

    for port in nmap.hosts[0].get_open_ports():
        tmpports.append(str(port[0]))
        srv = nmap.hosts[0].get_service(port[0], port[1])
        portinfo = srv.get_dict()
        portinfo["service"] = srv.service_dict
        portinfo["scripts"] = []
        for script in srv.scripts_results:
            scriptsave = {"id": script["id"], "output": script["output"]}
            portinfo["scripts"].append(scriptsave)
            if script["id"] == "ssl-cert":
                portinfo["ssl"] = parse_ssl_data(script)

        newhost["ports"].append(portinfo)

    newhost["port_str"] = ", ".join(tmpports)

    if "screenshots" in newhost and newhost["screenshots"]:
        newhost["screenshots"], newhost["num_screenshots"] = process_screenshots(
            newhost["screenshots"]
        )

    if len(newhost["ports"]) == 0:
        status_code = 200
        response_body = json.dumps(
            {
                "status": status_code,
                "message": f"Expected open ports but didn't find any for {newhost['ip']}",
            }
        )
    elif len(newhost["ports"]) > 500:
        status_code = 200
        response_body = json.dumps(
            {
                "status": status_code,
                "message": "More than 500 ports found, throwing data out",
            }
        )
    else:
        status_code = 200
        current_app.elastic.new_result(newhost)
        response_body = json.dumps(
            {
                "status": status_code,
                "message": f"Received {len(newhost['ports'])} ports for {newhost['ip']}",
            }
        )

    response = Response(
        response=response_body, status=status_code, content_type=json_content
    )
    return response


@bp.route("/natlas-services", methods=["GET"])
@is_agent_authenticated
def natlasServices():
    if current_app.current_services["id"] != "None":
        tmpdict = (
            current_app.current_services.copy()
        )  # make an actual copy of the dict so that we can remove the list
        del tmpdict[
            "as_list"
        ]  # don't return the "as_list" version of the services, which is only used for making a pretty table.
        response_body = json.dumps(tmpdict)
        status_code = 200
    else:
        response_body = json.dumps(current_app.current_services)
        status_code = 404
    return Response(
        response=response_body, status=status_code, content_type=json_content
    )


@bp.route("/status", methods=["GET"])
@is_authenticated
def status():
    last_cycle_start = current_app.ScopeManager.get_last_cycle_start()
    completed_cycles = current_app.ScopeManager.get_completed_cycle_count()
    avg_cycle_time = None
    if last_cycle_start:
        scans_this_cycle = current_app.elastic.count_scans_since(last_cycle_start)
        if completed_cycles > 0:
            delta = (
                last_cycle_start - current_app.ScopeManager.init_time
            ) / completed_cycles
            avg_cycle_time = pretty_time_delta(delta)
    else:
        scans_this_cycle = 0
    payload = {
        "natlas_start_time": current_app.ScopeManager.init_time,
        "cycle_start_time": last_cycle_start,
        "completed_cycles": completed_cycles,
        "scans_this_cycle": scans_this_cycle,
        "effective_scope_size": current_app.ScopeManager.get_effective_scope_size(),
        "avg_cycle_duration": avg_cycle_time,
    }
    return jsonify(payload)
