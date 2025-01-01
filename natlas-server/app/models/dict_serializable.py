class DictSerializable:
    def as_dict(self):  # type: ignore[no-untyped-def]
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}  # type: ignore[attr-defined]
