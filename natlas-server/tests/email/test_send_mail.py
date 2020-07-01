from flask import current_app

from app.email import send_email
from app.auth.email import send_auth_email
from app import mail


def test_send_mail(app):
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


def test_send_invite(app):
    test_token = "testinvitepleaseignore"
    with mail.record_messages() as outbox:
        send_auth_email("user@example.com", test_token, "invite")

    assert len(outbox) == 1
    assert outbox[0].subject == "[Natlas] You've been invited to Natlas!"
    assert test_token in outbox[0].body


def test_send_password_reset(app):
    test_token = "testresetpleaseignore"
    with mail.record_messages() as outbox:
        send_auth_email("user@example.com", test_token, "reset")

    assert len(outbox) == 1
    assert outbox[0].subject == "[Natlas] Reset Your Password"
    assert test_token in outbox[0].body
