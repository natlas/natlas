from flask import Flask
from netaddr import IPAddress
from netaddr.core import AddrFormatError
from werkzeug.routing import BaseConverter, ValidationError


class NatlasConverter(BaseConverter):
    pass


class IPConverter(NatlasConverter):
    name = "ip"

    def to_python(self, value: object) -> str:
        try:
            return str(IPAddress(value))
        except AddrFormatError as e:
            raise ValidationError from e


def register_converters(app: Flask) -> None:
    for converter in NatlasConverter.__subclasses__():
        app.url_map.converters[converter.name] = converter  # type: ignore[attr-defined]
