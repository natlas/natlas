import secrets

from pydantic import BaseModel

from app import db, elastic
from app.models import AgentConfig, NatlasServices, ScopeItem


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
        count, context = elastic.get_host_by_scan_id(rand)
        if count == 0:
            scan_id = rand
    return scan_id


class AgentConfigSerializer(BaseModel):
    id: int
    versionDetection: bool
    osDetection: bool
    enableScripts: bool
    onlyOpens: bool
    scanTimeout: int
    webScreenshots: bool
    vncScreenshots: bool
    webScreenshotTimeout: int
    vncScreenshotTimeout: int
    scriptTimeout: int
    hostTimeout: int
    osScanLimit: bool
    noPing: bool
    udpScan: bool | None
    scripts: str


class AgentWork(BaseModel):
    scan_reason: str
    target: str
    tags: list[str]
    type: str = "nmap"
    agent_config: AgentConfigSerializer
    services_hash: str
    scan_id: str
    status: int = 200
    message: str


def prepare_work(reason: str, target: str) -> AgentWork:
    services = db.session.get(NatlasServices, 1)
    if not services:
        raise RuntimeError("We have no services configured! What happened?!")
    config = db.session.get(AgentConfig, 1)
    if not config:
        raise RuntimeError("We have no agent config! What happened?!")
    config_dict = config.as_dict()
    config_dict.update(scripts=",".join(config.scripts))
    return AgentWork(
        scan_reason=reason,
        target=target,
        tags=get_target_tags(target),
        type="nmap",
        agent_config=AgentConfigSerializer.model_validate(config_dict),
        services_hash=services.sha256,
        scan_id=get_unique_scan_id(),
        status=200,
        message=f"Target: {target}",
    )
