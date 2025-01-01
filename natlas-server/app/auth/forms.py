from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from app.models import User


class LoginForm(FlaskForm):  # type: ignore[misc]
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):  # type: ignore[misc]
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

    def validate_email(self, email):  # type: ignore[no-untyped-def]
        user = User.query.filter_by(email=email.data.lower()).first()
        if user is not None:
            raise ValidationError("Email already exists!")


class ResetPasswordRequestForm(FlaskForm):  # type: ignore[misc]
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")


class ResetPasswordForm(FlaskForm):  # type: ignore[misc]
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Reset Password")


class AcceptInviteForm(FlaskForm):  # type: ignore[misc]
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Accept Invite")
