from flask_wtf import FlaskForm
from flask import flash
from flask_wtf.file import FileField
from wtforms import (
    StringField,
    BooleanField,
    SubmitField,
    TextAreaField,
    IntegerField,
    SelectField,
)
from wtforms.validators import DataRequired, ValidationError, Email
from app.models import User, ScopeItem, AgentScript
import ipaddress


class ConfigForm(FlaskForm):
    login_required = BooleanField("Login Required")
    register_allowed = BooleanField("Registration Allowed")
    agent_authentication = BooleanField("Agent Authentication Required")
    custom_brand = StringField("Custom Branding")
    submit = SubmitField("Save Changes")


class InviteUserForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Invite User")

    def validate_email(self, email):
        if not User.validate_email(email.data):
            flash(
                f"{email.data} does not appear to be a valid, deliverable email address.",
                "danger",
            )
            raise ValidationError
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            flash(f"Email {user.email} already exists!", "danger")
            raise ValidationError


class UserDeleteForm(FlaskForm):
    deleteUser = SubmitField("Delete User")


class UserEditForm(FlaskForm):
    editUser = SubmitField("Toggle Admin")


class NewScopeForm(FlaskForm):
    target = StringField("Target", validators=[DataRequired()])
    blacklist = BooleanField("Blacklist")
    submit = SubmitField("Add Target")

    def validate_target(self, target):
        try:
            isValid = ipaddress.ip_network(target.data, False)
            item = ScopeItem.query.filter_by(target=isValid.with_prefixlen).first()
            if item is not None:
                raise ValidationError(f"Target {item.target} already exists!")
        except ipaddress.AddressValueError as e:
            raise ValidationError(e)


class ImportScopeForm(FlaskForm):
    scope = TextAreaField("Scope Import", validators=[DataRequired()])
    submit = SubmitField("Import Scope")


class ImportBlacklistForm(FlaskForm):
    scope = TextAreaField("Blacklist Import", validators=[DataRequired()])
    submit = SubmitField("Import Blacklist")


class ScopeDeleteForm(FlaskForm):
    deleteScopeItem = SubmitField("Delete Target")


class ScopeToggleForm(FlaskForm):
    toggleScopeItem = SubmitField("Toggle Blacklist")


class ServicesUploadForm(FlaskForm):
    serviceFile = FileField("Select a file to upload", validators=[DataRequired()])
    uploadFile = SubmitField("Upload Services File")


class AddServiceForm(FlaskForm):
    serviceName = StringField("Service Name", validators=[DataRequired()])
    servicePort = IntegerField("Service Port", validators=[DataRequired()])
    serviceProtocol = SelectField("Protocol", validators=[DataRequired()])
    addService = SubmitField("Add Service")

    def validate_serviceName(self, serviceName):
        if " " in serviceName.data:
            raise ValidationError("Service names cannot contain spaces! Use - instead.")

    def validate_servicePort(self, servicePort):
        if servicePort.data > 65535 or servicePort.data < 0:
            raise ValidationError("Port has to be withing range of 0-65535")


class AgentConfigForm(FlaskForm):
    versionDetection = BooleanField("Version Detection (-sV)")
    osDetection = BooleanField("OS Detection (-O)")
    enableScripts = BooleanField("Scripting Engine (--script)")
    onlyOpens = BooleanField("Open Ports Only (--open)")
    scanTimeout = IntegerField("Maximum Nmap Run Time")
    webScreenshots = BooleanField("Web Screenshots (aquatone)")
    webScreenshotTimeout = IntegerField("Web Screenshot Timeout")
    vncScreenshots = BooleanField("VNC Screenshots (vncsnapshot)")
    vncScreenshotTimeout = IntegerField("VNC Screenshot Timeout")
    scriptTimeout = IntegerField("Script Timeout (--script-timeout)")
    hostTimeout = IntegerField("Host Timeout (--host-timeout)")
    osScanLimit = BooleanField("Limit OS Scan (--osscan-limit)")
    noPing = BooleanField("No Ping (-Pn)")
    udpScan = BooleanField("Also scan UDP (-sUS)")

    updateAgents = SubmitField("Update Agent Config")


class AddScriptForm(FlaskForm):
    scriptName = StringField("Script Name", validators=[DataRequired()])
    addScript = SubmitField("Add Script")

    def validate_scriptname(self, scriptName):
        script = AgentScript.query.filter_by(name=scriptName).first()
        if script is not None:
            raise ValidationError(f"{script.name} already exists!")


class DeleteForm(FlaskForm):
    delete = SubmitField("Delete")


class AddTagForm(FlaskForm):
    tagname = StringField("Tag Name", validators=[DataRequired()])
    addTag = SubmitField("Add Tag")


class TagScopeForm(FlaskForm):
    tagname = SelectField("Tag Name", validators=[DataRequired()])
    addTagToScope = SubmitField("Add Tag to Scope")
