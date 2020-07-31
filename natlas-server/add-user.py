#!/usr/bin/env python3
import argparse

from app import create_app, db
from app.models import User, UserInvitation
from config import Config

server_name_err = """[!] SERVER_NAME must be explicitly defined to use this script.
Try invoking like this: ./add-user.py --email example@example.com --admin --name example.com
Alternatively, set the SERVER_NAME environment variable."""


def parse_args():
    parser_desc = "Server-side utility to facilitate creating new users, especially for bootstrapping purposes."
    parser_epil = "An invitation link will be emailed to the user, or printed to the console if no mail server is configured."
    parser = argparse.ArgumentParser(description=parser_desc, epilog=parser_epil)
    parser.add_argument(
        "--email", metavar="example@example.com", help="Email address of user to create"
    )
    parser.add_argument(
        "--admin", action="store_true", default=False, help="Make the user an admin"
    )
    parser.add_argument(
        "--name",
        metavar="SERVER_NAME",
        help="Server name used to build invitation URLs. E.g. --name localhost:5000",
    )
    return parser.parse_args()


def new_invite(email=None, admin=False):
    invite = UserInvitation.new_invite(email=email, is_admin=admin)
    msg = UserInvitation.deliver_invite(invite)
    print(msg)


def user_exists(email):
    return User.query.filter_by(email=email).first() is not None


def handle_email_invite(email: str, admin: bool):
    validemail = User.validate_email(email)
    if not validemail:
        print(f"{email} does not appear to be a valid, deliverable email")
        return False
    if user_exists(validemail):
        print(f"User {validemail} already exists")
        return False
    new_invite(validemail, admin)
    db.session.commit()
    return True


def main(args):
    if args.email:
        return handle_email_invite(args.email, args.admin)
    else:
        new_invite(email=None, admin=args.admin)
        db.session.commit()
        return True


if __name__ == "__main__":
    args = parse_args()
    conf = Config()
    if args.name:
        conf.SERVER_NAME = args.name
    if not conf.SERVER_NAME:
        raise SystemExit(server_name_err)
    app = create_app(conf)
    with app.app_context():
        main(args)
