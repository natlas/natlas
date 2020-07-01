from app import db
import secrets
from datetime import timedelta, datetime
from app.models.dict_serializable import DictSerializable
from app.models.token_validation import validate_token
from app.models import User


class UserInvitation(db.Model, DictSerializable):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True)
    token = db.Column(db.String(32), unique=True, nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiration_date = db.Column(db.DateTime, nullable=False)
    accepted_date = db.Column(db.DateTime)
    is_expired = db.Column(db.Boolean, default=False)
    # is_admin should really only be used for bootstrapping users with add-user.py
    is_admin = db.Column(db.Boolean, default=False)

    # Tokens expire after 48 hours or upon use
    expiration_duration = 60 * 60 * 24 * 2
    token_length = 32

    # Build a new invitation
    @staticmethod
    def new_invite(email=None, is_admin=False):
        if email and User.query.filter_by(email=email).first():
            return False
        now = datetime.utcnow()
        expiration_date = now + timedelta(seconds=UserInvitation.expiration_duration)
        new_token = secrets.token_urlsafe(UserInvitation.token_length)
        invite = UserInvitation.query.filter_by(email=email).first()
        if invite and not invite.accepted_date:
            invite.token = new_token
            invite.expiration_date = expiration_date
        else:
            invite = UserInvitation(
                email=email,
                token=new_token,
                is_admin=is_admin,
                expiration_date=expiration_date,
            )
            db.session.add(invite)
        return invite

    @staticmethod
    def deliver_invite(invite):
        from flask import current_app, url_for
        from app.auth.email import send_auth_email

        if current_app.config.get("MAIL_SERVER", None) and invite.email:
            send_auth_email(invite.email, invite.token, "invite")
            msg = f"Invitation Sent to {invite.email}!"
        else:
            invite_url = url_for(
                "auth.invite_user",
                token=invite.token,
                _external=True,
                _scheme=current_app.config["PREFERRED_URL_SCHEME"],
            )
            msg = f"Share this link: {invite_url}"
        return msg

    @staticmethod
    def get_invite(url_token):
        record = UserInvitation.query.filter_by(token=url_token).first()
        if not record:
            return False
        return validate_token(record, url_token, record.token, record.validate_invite)

    def accept_invite(self):
        now = datetime.utcnow()
        self.accepted_date = now
        self.expire_invite(now)

    # If a token is expired, mark it as such
    def expire_invite(self, timestamp):
        if self.expiration_date >= timestamp:
            # Mark now as the expiration because it's been redeemed
            self.expiration_date = timestamp

        # Leave original expiration date intact since it's already past
        self.is_expired = True

    # verify that the token is not expired
    def validate_invite(self):
        now = datetime.utcnow()
        return self.expiration_date > now and not self.is_expired
