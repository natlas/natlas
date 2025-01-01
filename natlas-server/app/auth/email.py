from flask import current_app, flash, render_template, url_for

from app.email import send_email

token_types = {
    "reset": {
        "subject": "[Natlas] Reset Your Password",
        "template": "email/reset_password.txt",
        "route": "auth.reset_password",
    },
    "invite": {
        "subject": "[Natlas] You've been invited to Natlas!",
        "template": "email/user_invite.txt",
        "route": "auth.invite_user",
    },
}


def validate_email(addr):
    from app.models import User

    validemail = User.validate_email(addr)
    if not validemail:
        flash(
            f"{addr} does not appear to be a valid, deliverable email address.",
            "danger",
        )
        return None
    return validemail


def build_email_url(token, token_type):
    return url_for(
        token_types[token_type]["route"],
        token=token,
        _external=True,
        _scheme=current_app.config["PREFERRED_URL_SCHEME"],
    )


def email_configured() -> bool:
    return current_app.config["MAIL_FROM"] and current_app.config["MAIL_SERVER"]


def send_auth_email(email, token, token_type):
    send_email(
        token_types[token_type]["subject"],
        sender=current_app.config["MAIL_FROM"],
        recipients=[email],
        text_body=render_template(
            token_types[token_type]["template"], url=build_email_url(token, token_type)
        ),
    )


def deliver_auth_link(email: str, token: str, token_type: str):
    if email_configured() and email:
        send_auth_email(email, token, token_type)
        msg = f"Email sent to {email} via {current_app.config['MAIL_SERVER']}!"
    else:
        msg = f"Share this link: {build_email_url(token, token_type)}"
    return msg
