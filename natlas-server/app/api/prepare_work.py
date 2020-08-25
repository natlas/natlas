from flask import current_app
import secrets
from app.models import ScopeItem


def get_target_tags(target: str) -> list:
    overlap = ScopeItem.get_overlapping_ranges(target)
    tags = []
    for scope in overlap:
        tags.extend(scope.get_tag_names())
    return list(
        set(tags)
    )  # make it a set for only uniques, then make it a list to serialize to JSON


def get_unique_scan_id():
    scan_id = ""
    while scan_id == "":
        rand = secrets.token_hex(16)
        count, context = current_app.elastic.get_host_by_scan_id(rand)
        if count == 0:
            scan_id = rand
    return scan_id


def prepare_work(work):
    work["tags"] = get_target_tags(work["target"])
    work["type"] = "nmap"
    work["agent_config"] = current_app.agentConfig
    work["agent_config"]["scripts"] = current_app.agent_scripts
    work["services_hash"] = current_app.current_services["sha256"]
    work["scan_id"] = get_unique_scan_id()
    work["status"] = 200
    work["message"] = "Target: " + str(work["target"])
    return work
