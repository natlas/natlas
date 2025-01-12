import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import DateTime, String, select
from sqlalchemy.orm import Mapped, mapped_column

from app import NatlasBase, db
from app.models.dict_serializable import DictSerializable
from app.models.token_validation import validate_token


class UserInvitation(NatlasBase, DictSerializable):
    __tablename__ = "user_invitation"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(254), unique=True)
    token: Mapped[str] = mapped_column(String(256), unique=True)
    creation_date: Mapped[datetime | None] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    expiration_date: Mapped[datetime]
    accepted_date: Mapped[datetime | None]
    is_expired: Mapped[bool | None] = mapped_column(default=False)
    is_admin: Mapped[bool | None] = mapped_column(default=False)

    # Tokens expire after 48 hours or upon use
    expiration_duration = 60 * 60 * 24 * 2
    token_length = 32

    # Build a new invitation
    @staticmethod
    def new_invite(email: str | None, is_admin: bool = False) -> "UserInvitation":
        now = datetime.utcnow()
        expiration_date = now + timedelta(seconds=UserInvitation.expiration_duration)
        new_token = secrets.token_urlsafe(UserInvitation.token_length)
        invite = db.session.scalars(
            select(UserInvitation).where(UserInvitation.email == email)
        ).first()
        if email is not None and invite and not invite.accepted_date:
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
    def deliver_invite(invite: "UserInvitation") -> str:
        from app.auth.email import deliver_auth_link

        return deliver_auth_link(invite.email, invite.token, "invite")  # type: ignore[arg-type]

    @staticmethod
    def get_invite(url_token: str) -> Optional["UserInvitation"]:
        record = db.session.scalars(
            select(UserInvitation).where(UserInvitation.token == url_token)
        ).first()
        if record is None:
            return None
        return validate_token(record, url_token, record.token, record.validate_invite)

    def accept_invite(self) -> None:
        now = datetime.utcnow()
        self.accepted_date = now
        self.expire_invite(now)

    # If a token is expired, mark it as such
    def expire_invite(self, timestamp: datetime) -> None:
        self.expiration_date = min(timestamp, self.expiration_date)

        # Leave original expiration date intact since it's already past
        self.is_expired = True

    # verify that the token is not expired
    def validate_invite(self) -> bool:
        now = datetime.utcnow()
        return self.expiration_date > now and not self.is_expired
