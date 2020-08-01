from app.auth.email import deliver_auth_link
import click
from flask import current_app
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


@cli_group.command("role")
@click.argument("email", callback=validate_email)
@click.option("--promote/--demote", default=False)
def promote_user(email, promote):
    user = get_user(email)
    if user.is_admin == promote:
        print(f"{email} is already{' not ' if not promote else ' '}an admin")
        return
    user.is_admin = promote
    db.session.commit()
    print(f"{email} is {'now' if user.is_admin else 'no longer'} an admin")


@cli_group.command("reset-password")
@click.argument("email", callback=validate_email)
def reset_password(email):
    ensure_server_name()
    user = User.get_reset_token(email)
    if not user:
        raise click.BadParameter(err_msgs["no_such_user"].format(email))
    msg = deliver_auth_link(user.email, user.password_reset_token, "reset")
    db.session.commit()
    print(msg)
