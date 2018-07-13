from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import User, ScopeItem
import ipaddress

class LoginForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('Remember Me')
	submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already exists!')

class ResetPasswordRequestForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class InviteUserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Invite User')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email %s already exists!' % user.email)

class InviteConfirmForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Set Password')

class UserDeleteForm(FlaskForm):
    deleteUser = SubmitField('Delete User')

class UserEditForm(FlaskForm):
    editUser = SubmitField('Toggle Admin')

class NewScopeForm(FlaskForm):
    target = StringField('Target', validators=[DataRequired()])
    blacklist = BooleanField('Blacklist')
    submit = SubmitField('Add Target')

    def validate_target(self, target):
        item = ScopeItem.query.filter_by(target=target.data).first()
        if item is not None:
            raise ValidationError('Target %s already exists!' % item.target)
        try:
            isValid = ipaddress.IPv4Interface(target.data)
        except ipaddress.AddressValueError:
            raise ValidationError('Target %s couldn\'t be validated' % target.data)

class ScopeDeleteForm(FlaskForm):
    deleteScopeItem = SubmitField('Delete Target')

class ScopeToggleForm(FlaskForm):
    toggleScopeItem = SubmitField('Toggle Blacklist')