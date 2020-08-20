from flask import url_for, current_app

json_headers = {"Accept": "application/json"}
html_headers = {"Accept": "text/html"}
weighted_headers = {"Accept": "text/html;q=0.8, application/json"}

NONEXISTANT_URL = "/very_long_obviously_not_legitimate_url"


def test_404_error(client):
    expected_err_code = 404
    response = client.get(NONEXISTANT_URL)
    assert response.status_code == expected_err_code


def test_405_error(client):
    expected_err_code = 405
    response = client.delete("/")
    assert response.status_code == expected_err_code


def test_json_error(client):
    expected_err_code = 404
    expected_keys = ["status", "message"]
    response = client.get(NONEXISTANT_URL, headers=json_headers)
    assert response.content_type == "application/json; charset=utf-8"
    assert response.get_json()
    for key in expected_keys:
        assert key in response.get_json()
    assert response.get_json()["status"] == expected_err_code


def test_html_error(client):
    response = client.get(NONEXISTANT_URL, headers=html_headers)
    assert response.content_type == "text/html; charset=utf-8"


def test_content_type_matching(client):
    response = client.get(NONEXISTANT_URL, headers=weighted_headers)
    assert response.content_type == "application/json; charset=utf-8"


def test_invalid_search(client):
    invalid_query = "tags:!invalid"
    current_app.config["LOGIN_REQUIRED"] = False
    response = client.get(
        url_for("main.search", query=invalid_query), headers=json_headers
    )
    assert response.status_code == 400
    assert invalid_query in response.get_json()["message"]
