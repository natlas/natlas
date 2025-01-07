import secrets
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal, Optional

from email_validator import EmailNotValidError, ValidatedEmail, validate_email
from flask_login import UserMixin
from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login
from app.models.dict_serializable import DictSerializable
from app.models.token_validation import validate_token

if TYPE_CHECKING:
    from app.models.agent import Agent
    from app.models.rescan_task import RescanTask
    from app.models.user_invitation import UserInvitation


class User(UserMixin, db.Model, DictSerializable):  # type: ignore[misc, name-defined]
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(254), index=True, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(128))
    is_admin: Mapped[bool | None] = mapped_column(default=False)
    results_per_page: Mapped[int | None] = mapped_column(default=100)
    preview_length: Mapped[int | None] = mapped_column(default=100)
    result_format: Mapped[int | None] = mapped_column(default=0)
    password_reset_token: Mapped[str | None] = mapped_column(String(256), unique=True)
    password_reset_expiration: Mapped[datetime | None]
    creation_date: Mapped[datetime | None] = mapped_column(default=datetime.utcnow)
    is_active: Mapped[bool | None] = mapped_column(default=False)
    rescans: Mapped[list["RescanTask"]] = relationship(
        backref="submitter", lazy="select"
    )
    agents: Mapped[list["Agent"]] = relationship(backref="submitter", lazy="select")

    # Tokens expire after 48 hours or upon use
    expiration_duration = 60 * 60 * 24 * 2
    token_length = 32

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    @staticmethod
    def exists(email: str) -> bool:
        return (
            db.session.scalars(select(User).where(User.email == email)).first()
            is not None
        )

    # https://github.com/JoshData/python-email-validator
    @staticmethod
    def validate_email(email: str) -> ValidatedEmail | Literal[False]:
        try:
            valid = validate_email(email)
            return valid["email"]
        except EmailNotValidError:
            return False

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)  # type: ignore[arg-type]

    @login.user_loader  # type: ignore[misc]
    def load_user(id: int) -> "User":
        return db.session.get(User, id)  # type: ignore[return-value]

    def new_reset_token(self) -> None:
        self.password_reset_token = secrets.token_urlsafe(User.token_length)
        self.password_reset_expiration = datetime.utcnow() + timedelta(
            seconds=User.expiration_duration
        )

    def expire_reset_token(self) -> None:
        self.password_reset_token = None
        self.password_reset_expiration = None

    def validate_reset_token(self) -> bool:
        if not (self.password_reset_token and self.password_reset_expiration):
            return False
        return self.password_reset_expiration > datetime.utcnow()

    @staticmethod
    def get_reset_token(email: str) -> Optional["User"]:
        user = db.session.scalars(select(User).where(User.email == email)).first()
        if not user:
            return None
        if not user.validate_reset_token():
            user.new_reset_token()
        return user

    @staticmethod
    def get_user_by_token(url_token: str) -> Optional["User"]:
        record = db.session.scalars(
            select(User).where(User.password_reset_token == url_token)
        ).first()
        if not record:
            return None
        return validate_token(
            record,
            url_token,
            record.password_reset_token,  # type: ignore[arg-type]
            record.validate_reset_token,
        )

    @staticmethod
    def new_user_from_invite(
        invite: "UserInvitation", password: str, email: str | None = None
    ) -> "User":
        user_email = email if email else invite.email
        new_user = User(email=user_email, is_admin=invite.is_admin, is_active=True)
        new_user.set_password(password)
        invite.accept_invite()
        db.session.add(new_user)
        return new_user
