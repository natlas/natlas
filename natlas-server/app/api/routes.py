import json
from datetime import UTC
from datetime import datetime as dt

import dateutil.parser
from flask import Response, current_app, jsonify, request
from libnmap.parser import NmapParser, NmapParserException

from app import scope_manager
from app.api import bp
from app.api.prepare_work import prepare_work
from app.api.processing.screenshot import process_screenshots
from app.api.processing.ssl import parse_ssl_data
from app.api.rescan_handler import mark_scan_completed, mark_scan_dispatched
from app.auth.wrappers import is_agent_authenticated, is_authenticated
from app.util import pretty_time_delta

json_content = "application/json"


@bp.route("/getwork", methods=["GET"])
@is_agent_authenticated
def getwork() -> Response:
    manual = request.args.get("target", "")
    if "natlas-agent" in request.headers["user-agent"]:
        verstr = request.headers["user-agent"].split("/")[1]
        if verstr != current_app.config["NATLAS_VERSION"]:
            errmsg = f"The server detected you were running version {verstr} but the server is running {current_app.config['NATLAS_VERSION']}"
            response_body = json.dumps(
                {"status": 400, "message": errmsg, "retry": False}
            )
            return Response(
                response=response_body, status=400, content_type=json_content
            )
    if manual:
        canTarget = scope_manager.is_acceptable_target(manual)
        if canTarget:
            work = prepare_work(reason="manual", target=manual)
            response = Response(
                response=work.model_dump_json(), status=200, content_type=json_content
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

    rescans = scope_manager.get_pending_rescans()
    if (
        len(rescans) == 0
    ):  # If there aren't any rescans, update the Rescan Queue and get it again, because of lazy loading
        scope_manager.update_pending_rescans()
        rescans = scope_manager.get_pending_rescans()

    if len(rescans) == 0:  # if we don't have rescans, use the ScanManager
        scanmanager = scope_manager.get_scan_manager()

        if not scanmanager:
            response_body = json.dumps(
                {
                    "status": 404,
                    "message": "No scope is currently configured.",
                    "retry": True,
                }
            )
            return Response(
                response=response_body, status=404, content_type=json_content
            )
        work = prepare_work(reason="auto", target=str(scanmanager.get_next_ip()))

    else:  # Get the ip from the rescan queue, mark the job as dispatched, update the PendingRescans for other requests
        work = prepare_work(reason="requested", target=rescans[0].target)
        mark_scan_dispatched(rescans[0])

    response_body = work.model_dump_json()
    return Response(response=response_body, status=200, content_type=json_content)


@bp.route("/submit", methods=["POST"])
@is_agent_authenticated
def submit() -> Response:
    status_code = None
    response_body = None
    data = request.get_json()
    newhost = {}
    newhost = json.loads(data)
    newhost["ctime"] = dt.now(UTC)
    if newhost["scan_reason"] == "requested":
        mark_scan_completed(newhost["ip"], newhost["scan_id"])

    try:
        nmap = NmapParser.parse(newhost.get("xml_data", None))
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
        elif len(nmap.hosts) == 1 and not scope_manager.is_acceptable_target(
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
            current_app.elastic.new_result(newhost)  # type: ignore[attr-defined]
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
        return Response(
            response=response_body, status=status_code, content_type=json_content
        )

    if newhost["scan_start"] and newhost["scan_stop"]:
        elapsed = dateutil.parser.parse(newhost["scan_stop"]) - dateutil.parser.parse(
            newhost["scan_start"]
        )
        newhost["elapsed"] = elapsed.seconds

    newhost["ip"] = nmap.hosts[0].address  # type: ignore[possibly-undefined]
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

    if newhost.get("screenshots"):
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
        current_app.elastic.new_result(newhost)  # type: ignore[attr-defined]
        response_body = json.dumps(
            {
                "status": status_code,
                "message": f"Received {len(newhost['ports'])} ports for {newhost['ip']}",
            }
        )

    return Response(
        response=response_body, status=status_code, content_type=json_content
    )


@bp.route("/natlas-services", methods=["GET"])
@is_agent_authenticated
def natlasServices() -> Response:
    if current_app.current_services["id"] != "None":  # type: ignore[attr-defined]
        tmpdict = (
            current_app.current_services.copy()  # type: ignore[attr-defined]
        )  # make an actual copy of the dict so that we can remove the list
        del tmpdict[
            "as_list"
        ]  # don't return the "as_list" version of the services, which is only used for making a pretty table.
        response_body = json.dumps(tmpdict)
        status_code = 200
    else:
        response_body = json.dumps(current_app.current_services)  # type: ignore[attr-defined]
        status_code = 404
    return Response(
        response=response_body, status=status_code, content_type=json_content
    )


@bp.route("/status", methods=["GET"])
@is_authenticated
def status() -> Response:
    last_cycle_start = scope_manager.get_last_cycle_start()
    completed_cycles = scope_manager.get_completed_cycle_count()
    avg_cycle_time = None
    if last_cycle_start:
        scans_this_cycle = current_app.elastic.count_scans_since(last_cycle_start)  # type: ignore[attr-defined]
        if completed_cycles > 0 and scope_manager.init_time is not None:
            delta = (last_cycle_start - scope_manager.init_time) / completed_cycles
            avg_cycle_time = pretty_time_delta(delta)
    else:
        scans_this_cycle = 0
    payload = {
        "natlas_start_time": scope_manager.init_time,
        "cycle_start_time": last_cycle_start,
        "completed_cycles": completed_cycles,
        "scans_this_cycle": scans_this_cycle,
        "effective_scope_size": scope_manager.get_effective_scope_size(),
        "avg_cycle_duration": avg_cycle_time,
    }
    return jsonify(payload)
