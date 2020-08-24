from werkzeug.routing import BaseConverter, ValidationError
from netaddr import IPAddress
from netaddr.core import AddrFormatError
from flask import Flask


class NatlasConverter(BaseConverter):
    pass


class IPConverter(NatlasConverter):
    name = "ip"

    def to_python(self, value):
        try:
            return str(IPAddress(value))
        except AddrFormatError:
            raise ValidationError


def register_converters(app: Flask) -> dict:
    for converter in NatlasConverter.__subclasses__():
        app.url_map.converters[converter.name] = converter
