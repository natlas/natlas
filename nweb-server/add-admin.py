import argparse
from app import app, db
from app.models import User

parser = argparse.ArgumentParser()
parser.add_argument("email")
args = parser.parse_args()
user = User.query.filter_by(email=args.email).first()
user.is_admin=True
db.session.add(user)
db.session.commit()