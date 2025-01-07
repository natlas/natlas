import secrets

from flask import current_app

from app.models import ScopeItem


def get_target_tags(target: str) -> list[str]:
    overlap = ScopeItem.get_overlapping_ranges(target)
    tags = []
    for scope in overlap:
        tags.extend(scope.get_tag_names())
    return list(
        set(tags)
    )  # make it a set for only uniques, then make it a list to serialize to JSON


def get_unique_scan_id() -> str:
    scan_id = ""
    while scan_id == "":
        rand = secrets.token_hex(16)
        count, context = current_app.elastic.get_host_by_scan_id(rand)  # type: ignore[attr-defined]
        if count == 0:
            scan_id = rand
    return scan_id


def prepare_work(work):  # type: ignore[no-untyped-def]
    work["tags"] = get_target_tags(work["target"])
    work["type"] = "nmap"
    work["agent_config"] = current_app.agentConfig  # type: ignore[attr-defined]
    work["agent_config"]["scripts"] = current_app.agent_scripts  # type: ignore[attr-defined]
    work["services_hash"] = current_app.current_services["sha256"]  # type: ignore[attr-defined]
    work["scan_id"] = get_unique_scan_id()
    work["status"] = 200
    work["message"] = "Target: " + str(work["target"])
    return work
