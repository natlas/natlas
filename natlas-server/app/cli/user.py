from app.auth.email import send_auth_email
import click
from flask import current_app, url_for
from flask.cli import AppGroup

from app import db
from app.models import User, UserInvitation

cli_group = AppGroup("user")

err_msgs = {
    "invalid_email": "{} does not appear to be a valid, deliverable email",
    "server_name": "SERVER_NAME environment variable is requried to perform this action",
    "user_exists": "{} already exists",
    "no_such_user": "{} doesn't exist",
}


def get_user(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        raise click.BadParameter(err_msgs["no_such_user"].format(email))
    return user


def validate_email(ctx, param, value):
    if not value:
        return
    valid_email = User.validate_email(value)
    if not valid_email:
        raise click.BadParameter(err_msgs["invalid_email"].format(value))
    return valid_email


def ensure_server_name():
    if not current_app.config["SERVER_NAME"]:
        raise click.UsageError(err_msgs["server_name"])


@cli_group.command("new")
@click.option("--email", callback=validate_email, default=None)
@click.option("--admin", is_flag=True, default=False)
def new_user(email, admin):
    ensure_server_name()

    if email and User.exists(email):
        raise click.BadParameter(f"{email} already exists")

    invite = UserInvitation.new_invite(email=email, is_admin=admin)
    msg = UserInvitation.deliver_invite(invite)
    db.session.commit()
    print(msg)


@cli_group.command("promote")
@click.argument("email", callback=validate_email)
def promote_user(email):
    user = get_user(email)
    msg = f"{email} is {'now' if not user.is_admin else 'already'} an admin"
    user.is_admin = True
    db.session.commit()
    print(msg)


@cli_group.command("demote")
@click.argument("email", callback=validate_email)
def demote_user(email):
    user = get_user(email)
    msg = f"{email} is {'not' if not user.is_admin else 'no longer'} an admin"
    user.is_admin = False
    db.session.commit()
    print(msg)


@cli_group.command("reset-password")
@click.argument("email", callback=validate_email)
def reset_password(email):
    ensure_server_name()
    user = User.get_reset_token(email)
    if not user:
        raise click.BadParameter(err_msgs["no_such_user"].format(email))
    if current_app.config.get("MAIL_SERVER", None):
        send_auth_email(user.email, user.password_reset_token, "invite")
        msg = f"Invitation Sent to {user.email}!"
    else:
        reset_url = url_for(
            "auth.reset_password",
            token=user.password_reset_token,
            _external=True,
            _scheme=current_app.config["PREFERRED_URL_SCHEME"],
        )
        msg = f"Share this link: {reset_url}"
    db.session.commit()
    print(msg)
