from datetime import UTC, datetime


class ScanResult:
    def __init__(self, target_data, config):  # type: ignore[no-untyped-def]
        self.result = {
            "ip": target_data["target"],
            "scan_reason": target_data["scan_reason"],
            "tags": target_data["tags"],
            "scan_id": target_data["scan_id"],
            "agent_version": config.NATLAS_VERSION,
            "agent": config.agent_id or "anonymous",
            "scan_start": datetime.now(UTC).isoformat(),
        }

    def add_item(self, name, value):  # type: ignore[no-untyped-def]
        self.result[name] = value

    def scan_stop(self):  # type: ignore[no-untyped-def]
        self.result["scan_stop"] = datetime.now(UTC).isoformat()

    def is_up(self, status):  # type: ignore[no-untyped-def]
        self.result["is_up"] = status

    def add_screenshot(self, screenshot):  # type: ignore[no-untyped-def]
        if "screenshots" not in self.result:
            self.result["screenshots"] = []
        self.result["screenshots"].append(screenshot)
