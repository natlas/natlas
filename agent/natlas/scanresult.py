from datetime import UTC, datetime
from typing import Any

from config import Config
from pydantic import BaseModel, Field

from natlas.screenshot_models import AquatoneScreenshot, VNCScreenshot


class NewScanResult(BaseModel):
    """
    This is a rough first pass at turning ScanResult into a pydantic model

    Unfortunately the way I just yoloed this data structure before as a wrapper for a dict
    means that switching over to a pydantic model is going to be a little difficult.

    But it's doable.
    """

    ip: str
    scan_reason: str
    tags: list[str]
    scan_id: str
    agent_version: str
    agent: str = "anonymous"
    scan_start: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    scan_stop: str
    timed_out: bool = False
    nmap_data: str
    gnmap_data: str
    xml_data: str
    port_count: int
    is_up: bool
    screenshots: list[AquatoneScreenshot | VNCScreenshot]


class ScanResult:
    def __init__(self, target_data: dict[str, Any], config: Config) -> None:
        self.result = {
            "ip": target_data["target"],
            "scan_reason": target_data["scan_reason"],
            "tags": target_data["tags"],
            "scan_id": target_data["scan_id"],
            "agent_version": config.NATLAS_VERSION,
            "agent": config.agent_id if config.agent_id else "anonymous",
            "scan_start": datetime.now(UTC).isoformat(),
        }

    def add_item(self, name: str, value: Any) -> None:
        self.result[name] = value

    def scan_stop(self) -> None:
        self.result["scan_stop"] = datetime.now(UTC).isoformat()

    def is_up(self, status: bool) -> None:
        self.result["is_up"] = status

    def add_screenshot(self, screenshot: AquatoneScreenshot | VNCScreenshot) -> None:
        if "screenshots" not in self.result:
            self.result["screenshots"] = []
        self.result["screenshots"].append(screenshot.model_dump())
