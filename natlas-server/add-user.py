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
    parser_desc = "Server-side utility to facilitate creating users. This is only meant to be used for bootstrapping, \
        as it prints the password to the command line."
    parser_epil = "Be sure that you're running this from within the virtual environment for the server, \
        otherwise it will almost certainly fail."
    parser = argparse.ArgumentParser(description=parser_desc, epilog=parser_epil)
    parser.add_argument("email", metavar="example@example.com", help="Email address of user to create or modify")
    parser.add_argument("--admin", action="store_true", default=False, help="Use this flag to make the user admin")
    args = parser.parse_args()
    user = User.query.filter_by(email=args.email.lower()).first()
    if user is not None:
        if args.admin:
            if user.is_admin:
                print("User %s is already an admin" % args.email.lower())
                return
            else:
                user.is_admin = True
                db.session.add(user)
                db.session.commit()
                print("User %s is now an admin" % args.email.lower())
                return
        else:
            print("User %s already exists" % args.email.lower())
            return
    else:
        password=''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(PASS_LENGTH))
        user = User(email=args.email.lower(), is_admin=args.admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        if user.is_admin:
            admintext = " as an admin "
        else:
            admintext = " "
        print("User %s has been created%swith password %s" % (args.email.lower(), admintext, password))
        return

if __name__ == "__main__":
    main()