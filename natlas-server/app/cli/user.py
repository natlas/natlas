import click
from email_validator import ValidatedEmail
from flask import current_app
from flask.cli import AppGroup
from sqlalchemy import select

from app import db
from app.auth.email import deliver_auth_link
from app.models import User, UserInvitation

cli_group = AppGroup("user")

err_msgs = {
    "invalid_email": "{} does not appear to be a valid, deliverable email",
    "server_name": "SERVER_NAME environment variable is requried to perform this action",
    "user_exists": "{} already exists",
    "no_such_user": "{} doesn't exist",
}


def get_user(email: str) -> User:
    user = db.session.scalars(select(User).where(User.email == email)).first()
    if not user:
        raise click.BadParameter(err_msgs["no_such_user"].format(email))
    return user


def validate_email(_ctx: object, _param: object, value: str) -> ValidatedEmail | None:
    """
    I have no idea what the ctx, param, and value types are. I'm sure click documents it somewhere but idk.
    I'm just marking them as object because we don't use them anyways.
    """
    if not value:
        return None
    valid_email = User.validate_email(value)
    if not valid_email:
        raise click.BadParameter(err_msgs["invalid_email"].format(value))
    return valid_email


def ensure_server_name() -> None:
    if not current_app.config["SERVER_NAME"]:
        raise click.UsageError(err_msgs["server_name"])


@cli_group.command("new")
@click.option("--email", callback=validate_email)
@click.option("--admin", is_flag=True, default=False)
def new_user(email: str, admin: bool) -> None:
    ensure_server_name()

    if email and User.exists(email):
        raise click.BadParameter(f"{email} already exists")

    invite = UserInvitation.new_invite(email=email, is_admin=admin)
    msg = UserInvitation.deliver_invite(invite)
    db.session.commit()
    print(msg)


@cli_group.command("role")
@click.argument("email", callback=validate_email)
@click.option("--promote/--demote", default=False)
def promote_user(email: str, promote: bool) -> None:
    user = get_user(email)
    if user.is_admin == promote:
        print(f"{email} is already{' not ' if not promote else ' '}an admin")
        return
    user.is_admin = promote
    db.session.commit()
    print(f"{email} is {'now' if user.is_admin else 'no longer'} an admin")


@cli_group.command("reset-password")
@click.argument("email", callback=validate_email)
def reset_password(email: str) -> None:
    ensure_server_name()
    user = User.get_reset_token(email)
    if not user:
        raise click.BadParameter(err_msgs["no_such_user"].format(email))
    msg = deliver_auth_link(user.email, user.password_reset_token, "reset")  # type: ignore[arg-type]
    db.session.commit()
    print(msg)
