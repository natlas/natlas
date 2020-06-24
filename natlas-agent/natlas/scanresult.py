from datetime import datetime, timezone


class ScanResult:
    def __init__(self, target_data, config):
        self.result = {
            "ip": target_data["target"],
            "scan_reason": target_data["scan_reason"],
            "tags": target_data["tags"],
            "scan_id": target_data["scan_id"],
            "agent_version": config.NATLAS_VERSION,
            "agent": config.agent_id if config.agent_id else "anonymous",
            "scan_start": datetime.now(timezone.utc).isoformat(),
        }

    def add_item(self, name, value):
        self.result[name] = value

    def scan_stop(self):
        self.result["scan_stop"] = datetime.now(timezone.utc).isoformat()

    def is_up(self, status):
        self.result["is_up"] = status

    def add_screenshot(self, screenshot):
        if "screenshots" not in self.result:
            self.result["screenshots"] = []
        self.result["screenshots"].append(screenshot)
