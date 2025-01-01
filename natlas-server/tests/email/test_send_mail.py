from app import mail
from app.auth.email import deliver_auth_link
from app.email import send_email
from flask import current_app


def test_send_mail(app):  # type: ignore[no-untyped-def]
    with mail.record_messages() as outbox:
        send_email(
            "Natlas Test Mail",
            current_app.config["MAIL_FROM"],
            ["user@example.com"],
            "You've got mail!",
        )
    assert len(outbox) == 1
    assert outbox[0].subject == "Natlas Test Mail"
    assert outbox[0].sender == current_app.config["MAIL_FROM"]


def test_send_invite(app):  # type: ignore[no-untyped-def]
    test_token = "testinvitepleaseignore"
    with mail.record_messages() as outbox:
        result = deliver_auth_link("user@example.com", test_token, "invite")

    assert len(outbox) == 1
    assert outbox[0].subject == "[Natlas] You've been invited to Natlas!"
    assert test_token in outbox[0].body
    assert test_token not in result


def test_send_password_reset(app):  # type: ignore[no-untyped-def]
    test_token = "testresetpleaseignore"
    with mail.record_messages() as outbox:
        result = deliver_auth_link("user@example.com", test_token, "reset")

    assert len(outbox) == 1
    assert outbox[0].subject == "[Natlas] Reset Your Password"
    assert test_token in outbox[0].body
    assert test_token not in result


def test_password_reset_no_email(app_no_email):  # type: ignore[no-untyped-def]
    test_token = "testresetpleaseignore"
    email = "user@example.com"
    result = deliver_auth_link(email, test_token, "reset")
    assert test_token in result
    assert email not in result


def test_invite_no_email(app_no_email):  # type: ignore[no-untyped-def]
    test_token = "testinvitepleaseignore"
    email = "user@example.com"
    result = deliver_auth_link(email, test_token, "invite")
    assert test_token in result
    assert email not in result
