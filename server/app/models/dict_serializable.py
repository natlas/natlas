from typing import Any


class DictSerializable:
    def as_dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}  # type: ignore[attr-defined]
