#!/usr/bin/env python3
import argparse
import random
import string
from app import create_app, db
from app.models import User

app = create_app()
app.app_context().push()

pass_length = 16

parser = argparse.ArgumentParser()
parser.add_argument("email")
args = parser.parse_args()
user = User.query.filter_by(email=args.email).first()
if user is not None:
	user.is_admin = True
	db.session.add(user)
	db.session.commit()
	print("User %s is now an admin" % args.email)
else:
	password=''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(pass_length))
	user = User(email=args.email, is_admin=True)
	user.set_password(password)
	db.session.add(user)
	db.session.commit()
	print("User %s has been created as an admin with password %s" % (args.email, password))