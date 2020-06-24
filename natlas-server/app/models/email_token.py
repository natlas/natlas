from app import db
from app.util import utcnow_tz, generate_hex_32
from datetime import datetime, timedelta
from app.models.dict_serializable import DictSerializable


class EmailToken(db.Model, DictSerializable):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(32), index=False, unique=True, nullable=False)
    date_generated = db.Column(db.DateTime, nullable=False, default=utcnow_tz)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Valid Token Types are: "register", "invite", and "reset"
    token_type = db.Column(db.String(8), index=True, nullable=False)
    token_expiration = db.Column(db.DateTime, nullable=False)

    # Build a new token
    @staticmethod
    def new_token(user_id, token_type):
        supported_token_types = {
            "invite": 60 * 60 * 24 * 2,  # 48 hours
            "reset": 60 * 10,  # 10 minutes
        }
        if token_type not in supported_token_types:
            return False
        expiration = utcnow_tz() + timedelta(seconds=supported_token_types[token_type])
        hasToken = EmailToken.query.filter_by(
            user_id=user_id, token_type=token_type
        ).first()
        if hasToken:
            EmailToken.expire_token(hasToken)

        newToken = EmailToken(
            user_id=user_id,
            token=generate_hex_32(),
            token_type=token_type,
            token_expiration=expiration,
        )
        db.session.add(newToken)
        db.session.commit()
        return newToken

    # Get token from database
    @staticmethod
    def get_token(token):
        mytoken = EmailToken.query.filter_by(token=token).first()
        if mytoken:
            return mytoken
        else:
            return False

    # If a token is expired, I don't want to bother keeping it.
    # Keep as little information about users as necessary, old tokens aren't necessary
    @staticmethod
    def expire_token(token=None, tokenstr=None):
        if token:
            db.session.delete(token)
            db.session.commit()
            return True
        elif tokenstr:
            mytoken = EmailToken.get_token(tokenstr)
            if not mytoken:
                # token already doesn't exist
                return True
            db.session.delete(mytoken)
            db.session.commit()
            return True
        else:
            return False

    # verify that the token is not expired and is of the correct token type
    def verify_token(self, ttype):
        if self.token_expiration > datetime.utcnow():
            if self.token_type == ttype:
                # Expiration date is in the future and token type matches expected
                return True
            else:
                # The token type didn't match, which would only happen if someone tries to use a token for the wrong reason
                return False
        else:
            # The token has expired, delete it
            EmailToken.expire_token(token=self)
            return False
