from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, ValidationError, EqualTo, Length
from app.models import User


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Old Password", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    changePassword = SubmitField("Change Password")

    def validate_old_password(self, old_password):
        user = User.query.get(current_user.id)
        if user is None:
            raise ValidationError("You're not logged in!")
        if not user.check_password(old_password.data):
            raise ValidationError(
                "Invalid password! If you forgot your password, please use the password reset form."
            )


class DisplaySettingsForm(FlaskForm):
    results_per_page = SelectField("Results Per Page", coerce=int)
    preview_length = SelectField("Preview Length", coerce=int)
    result_format = SelectField("Result Format", coerce=int)
    updateDisplaySettings = SubmitField("Submit Changes")


class GenerateTokenForm(FlaskForm):
    generateToken = SubmitField("Generate Token")


class AgentNameForm(FlaskForm):
    agent_name = StringField("New Agent Name", validators=[DataRequired()])
    change_name = SubmitField("Change Name")

    def validate_agent_name(self, agent_name):
        if len(agent_name.data) > 32:
            raise ValidationError("Name must be less than 32 characters")
