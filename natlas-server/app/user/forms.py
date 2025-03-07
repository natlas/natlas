from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError

from app import db
from app.models import User


class ChangePasswordForm(FlaskForm):  # type: ignore[misc]
    old_password = PasswordField("Old Password", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    changePassword = SubmitField("Change Password")

    def validate_old_password(self, old_password: PasswordField) -> None:
        user = db.session.get(User, current_user.id)
        if user is None:
            raise ValidationError("You're not logged in!")
        if not user.check_password(old_password.data):
            raise ValidationError(
                "Invalid password! If you forgot your password, please use the password reset form."
            )


class DisplaySettingsForm(FlaskForm):  # type: ignore[misc]
    results_per_page = SelectField("Results Per Page", coerce=int)
    preview_length = SelectField("Preview Length", coerce=int)
    result_format = SelectField("Result Format", coerce=int)
    updateDisplaySettings = SubmitField("Submit Changes")


class GenerateTokenForm(FlaskForm):  # type: ignore[misc]
    generateToken = SubmitField("Generate Token")


class AgentNameForm(FlaskForm):  # type: ignore[misc]
    agent_name = StringField("New Agent Name", validators=[DataRequired()])
    change_name = SubmitField("Change Name")

    def validate_agent_name(self, agent_name: StringField) -> None:
        if len(agent_name.data) > 32:
            raise ValidationError("Name must be less than 32 characters")
