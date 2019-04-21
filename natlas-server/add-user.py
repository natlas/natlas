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

    validemail = User.validate_email(args.email)

    if not validemail:
        print("%s does not appear to be a valid, deliverable email" % args.email)
        return

    user = User.query.filter_by(email=validemail).first()
    if user is not None:
        if args.admin:
            if user.is_admin:
                print("User %s is already an admin" % validemail)
                return
            else:
                user.is_admin = True
                db.session.add(user)
                db.session.commit()
                print("User %s is now an admin" % validemail)
                return
        else:
            print("User %s already exists" % validemail)
            return
    else:
        password=User.generate_password(PASS_LENGTH)
        user = User(email=validemail, is_admin=args.admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        if user.is_admin:
            admintext = " as an admin "
        else:
            admintext = " "
        print("User %s has been created%swith password %s" % (validemail, admintext, password))
        return

if __name__ == "__main__":
    main()