import json


class NatlasServiceError(Exception):
    def __init__(self, status_code: int, message: str, template: str | None = None):
        self.status_code = status_code
        self.message = message
        self.template = template if template else f"errors/{self.status_code}.html"

    def __str__(self) -> str:
        return f"{self.status_code}: {self.message}"

    def get_dict(self) -> dict[str, int | str]:
        return {"status": self.status_code, "message": self.message}

    def get_json(self) -> str:
        return json.dumps(self.get_dict(), sort_keys=True, indent=4)


class NatlasSearchError(NatlasServiceError):
    def __init__(self, e):  # type: ignore[no-untyped-def]
        self.status_code = 400
        self.message = e.info["error"]["root_cause"][0]["reason"]
        self.template = "errors/search.html"
