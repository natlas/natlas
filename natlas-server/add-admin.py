#!/usr/bin/env python3
import argparse
import random
import string
from app import create_app, db
from app.models import User

app = create_app()
app.app_context().push()

PASS_LENGTH = 16

def main():
	parser_desc = "Server-side utility to facilitate creating admins and toggling existing users to admins."
	parser_epil = "Be sure that you're running this from within the virtual environment for the server."
	parser = argparse.ArgumentParser()
	parser.add_argument("email", metavar="example@example.com", help="email address to make admin")
	args = parser.parse_args()
	user = User.query.filter_by(email=args.email).first()
	if user is not None:
		if user.is_admin:
			print("User %s is already an admin" % args.email)
			return
		user.is_admin = True
		db.session.add(user)
		db.session.commit()
		print("User %s is now an admin" % args.email)
		return
	else:
		password=''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(PASS_LENGTH))
		user = User(email=args.email, is_admin=True)
		user.set_password(password)
		db.session.add(user)
		db.session.commit()
		print("User %s has been created as an admin with password %s" % (args.email, password))
		return

if __name__ == "__main__":
	main()