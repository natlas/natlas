#!/usr/bin/env python3
import argparse
from app import create_app, db
from app.models import User, UserInvitation
from flask import url_for, current_app
from app.auth.email import send_auth_email

PASS_LENGTH = 16


def make_user_admin(user):
	if user.is_admin:
		print(f"User {user.email} is already an admin")
		return
	else:
		user.is_admin = True
		print(f"User {user.email} is now an admin")
		return


# Create a new invitation because no user with supplied email exists
def new_invite(email=None, admin=False):
	invite = UserInvitation.new_invite(email=email, is_admin=admin)
	if current_app.config.get('MAIL_SERVER', None) and email:
		send_auth_email(email, invite.token, 'invite')
		print(f"Sent {email} an invitation email via {current_app.config['MAIL_SERVER']}")
	else:
		invite_url = url_for('auth.invite_user', token=invite.token, _external=True, _scheme=current_app.config['PREFERRED_URL_SCHEME'])
		print(f"Accept invitation: {invite_url}")


def main():
	parser_desc = "Server-side utility to facilitate creating users. This is only meant to be used for bootstrapping, \
		as it prints the password to the command line."
	parser_epil = "Be sure that you're running this from within the virtual environment for the server, \
		otherwise it will almost certainly fail."
	parser = argparse.ArgumentParser(description=parser_desc, epilog=parser_epil)
	parser.add_argument("--email", metavar="example@example.com", help="Email address of user to create or modify")
	parser.add_argument("--admin", action="store_true", default=False, help="Use this flag to make the user admin")
	args = parser.parse_args()
	if args.email:
		validemail = User.validate_email(args.email)
		if not validemail:
			print(f"{args.email} does not appear to be a valid, deliverable email")
			return
		user = User.query.filter_by(email=validemail).first()
		if user:
			if args.admin:
				make_user_admin(user)
				db.session.commit()
			else:
				print(f"User {validemail} already exists")
				return
		else:
			new_invite(args.email, args.admin)
			db.session.commit()
	else:
		new_invite(email=None, admin=args.admin)
		db.session.commit()
		return


if __name__ == "__main__":
	app = create_app()
	with app.app_context():
		main()
