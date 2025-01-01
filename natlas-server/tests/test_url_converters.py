import pytest
from app.url_converters import register_converters
from flask import Flask, abort

TEST_IP_ADDRS = ["127.0.0.1", "::1"]


@pytest.fixture
def converter_client():  # type: ignore[no-untyped-def]
    app = Flask(__name__)
    register_converters(app)

    @app.route("/ip/<ip:ip>")
    def ip_route(ip):  # type: ignore[no-untyped-def]
        if ip in TEST_IP_ADDRS:
            return ip
        # abort 400 to differentiate from an invalid ip 404 status code
        return abort(400)

    with app.app_context(), app.test_client() as client:
        yield client


def test_ip_converter(converter_client):  # type: ignore[no-untyped-def]
    assert converter_client.get("/ip/127.0.0.1").status_code == 200
    assert converter_client.get("/ip/::1").status_code == 200
    assert converter_client.get("/ip/254.254.254.254").status_code == 400
    assert converter_client.get("/ip/127.0.0.1asdf").status_code == 404
