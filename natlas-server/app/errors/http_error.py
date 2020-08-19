import json


class HTTPError:
    def __init__(self, status_code: int, message: str, template: str = None):
        self.status_code = status_code
        self.message = message
        self.template = f"errors/{self.status_code}.html" if not template else template

    def __str__(self):
        return f"{self.status_code}: {self.message}"

    def get_dict(self):
        return {"status": self.status_code, "message": self.message}

    def get_json(self):
        return json.dumps(self.get_dict(), sort_keys=True, indent=4)
