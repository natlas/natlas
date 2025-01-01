import ipaddress

from flask import flash
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import (
    BooleanField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, ValidationError

from app.models import AgentScript, ScopeItem, User


class ConfigForm(FlaskForm):  # type: ignore[misc]
    login_required = BooleanField("Login Required")
    register_allowed = BooleanField("Registration Allowed")
    agent_authentication = BooleanField("Agent Authentication Required")
    custom_brand = StringField("Custom Branding")
    submit = SubmitField("Save Changes")


class InviteUserForm(FlaskForm):  # type: ignore[misc]
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Invite User")

    def validate_email(self, email):  # type: ignore[no-untyped-def]
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


class UserDeleteForm(FlaskForm):  # type: ignore[misc]
    deleteUser = SubmitField("Delete User")


class UserEditForm(FlaskForm):  # type: ignore[misc]
    editUser = SubmitField("Toggle Admin")


class NewScopeForm(FlaskForm):  # type: ignore[misc]
    target = StringField("Target", validators=[DataRequired()])
    blacklist = BooleanField("Blacklist")
    submit = SubmitField("Add Target")

    def validate_target(self, target):  # type: ignore[no-untyped-def]
        try:
            isValid = ipaddress.ip_network(target.data, False)
            item = ScopeItem.query.filter_by(target=isValid.with_prefixlen).first()
            if item is not None:
                raise ValidationError(f"Target {item.target} already exists!")
        except ipaddress.AddressValueError as e:
            raise ValidationError(e) from e


class ImportScopeForm(FlaskForm):  # type: ignore[misc]
    scope = TextAreaField("Scope Import", validators=[DataRequired()])
    submit = SubmitField("Import Scope")


class ImportBlacklistForm(FlaskForm):  # type: ignore[misc]
    scope = TextAreaField("Blacklist Import", validators=[DataRequired()])
    submit = SubmitField("Import Blacklist")


class ScopeDeleteForm(FlaskForm):  # type: ignore[misc]
    deleteScopeItem = SubmitField("Delete Target")


class ScopeToggleForm(FlaskForm):  # type: ignore[misc]
    toggleScopeItem = SubmitField("Toggle Blacklist")


class ServicesUploadForm(FlaskForm):  # type: ignore[misc]
    serviceFile = FileField("Select a file to upload", validators=[DataRequired()])
    uploadFile = SubmitField("Upload Services File")


class AddServiceForm(FlaskForm):  # type: ignore[misc]
    serviceName = StringField("Service Name", validators=[DataRequired()])
    servicePort = IntegerField("Service Port", validators=[DataRequired()])
    serviceProtocol = SelectField("Protocol", validators=[DataRequired()])
    addService = SubmitField("Add Service")

    def validate_serviceName(self, serviceName):  # type: ignore[no-untyped-def]
        if " " in serviceName.data:
            raise ValidationError("Service names cannot contain spaces! Use - instead.")

    def validate_servicePort(self, servicePort):  # type: ignore[no-untyped-def]
        if servicePort.data > 65535 or servicePort.data < 0:
            raise ValidationError("Port has to be withing range of 0-65535")


class AgentConfigForm(FlaskForm):  # type: ignore[misc]
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


class AddScriptForm(FlaskForm):  # type: ignore[misc]
    scriptName = StringField("Script Name", validators=[DataRequired()])
    addScript = SubmitField("Add Script")

    def validate_scriptname(self, scriptName):  # type: ignore[no-untyped-def]
        script = AgentScript.query.filter_by(name=scriptName).first()
        if script is not None:
            raise ValidationError(f"{script.name} already exists!")


class DeleteForm(FlaskForm):  # type: ignore[misc]
    delete = SubmitField("Delete")


class AddTagForm(FlaskForm):  # type: ignore[misc]
    tagname = StringField("Tag Name", validators=[DataRequired()])
    addTag = SubmitField("Add Tag")


class TagScopeForm(FlaskForm):  # type: ignore[misc]
    tagname = SelectField("Tag Name", validators=[DataRequired()])
    addTagToScope = SubmitField("Add Tag to Scope")
