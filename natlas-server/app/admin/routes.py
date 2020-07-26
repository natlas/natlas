import ipaddress

from flask import (
    render_template,
    redirect,
    url_for,
    current_app,
    flash,
    Response,
    abort,
)
from flask_login import current_user, login_required

from app import db
from app.admin import bp
from app.admin import forms, redirects
from app.models import (
    User,
    ScopeItem,
    ConfigItem,
    NatlasServices,
    AgentConfig,
    AgentScript,
    Tag,
    ScopeLog,
    UserInvitation,
)
from app.auth.wrappers import is_admin


@bp.route("/", methods=["GET", "POST"])
@login_required
@is_admin
def admin():
    configForm = forms.ConfigForm()
    configItems = current_app.config
    if configForm.validate_on_submit():
        for fieldname, fieldvalue in configForm.data.items():
            if fieldname.upper() in ["SUBMIT", "CSRF_TOKEN"]:
                continue
            current_app.config[fieldname.upper()] = fieldvalue
            confitem = ConfigItem.query.filter_by(name=fieldname.upper()).first()
            confitem.value = str(fieldvalue)
            db.session.add(confitem)
        db.session.commit()
    return render_template(
        "admin/index.html", configForm=configForm, configItems=configItems
    )


@bp.route("/users", methods=["GET", "POST"])
@login_required
@is_admin
def users():
    users = User.query.all()
    inviteForm = forms.InviteUserForm()
    if inviteForm.validate_on_submit():
        invitation = UserInvitation.new_invite(inviteForm.email.data)
        msg = UserInvitation.deliver_invite(invitation)
        flash(msg, "success")
        db.session.commit()
        return redirect(url_for("admin.users"))
    return render_template(
        "admin/users.html",
        users=users,
        delForm=forms.UserDeleteForm(),
        editForm=forms.UserEditForm(),
        inviteForm=inviteForm,
    )


@bp.route("/users/<int:id>/delete", methods=["POST"])
@login_required
@is_admin
def delete_user(id):
    delForm = forms.UserDeleteForm()
    if delForm.validate_on_submit():
        if current_user.id == id:
            flash("You can't delete yourself!", "danger")
            return redirect(url_for("admin.users"))
        user = User.query.filter_by(id=id).first()
        User.query.filter_by(id=id).delete()
        db.session.commit()
        flash(f"{user.email} deleted!", "success")
    else:
        flash("Form couldn't validate!", "danger")

    return redirect(url_for("admin.users"))


@bp.route("/users/<int:id>/toggle", methods=["POST"])
@login_required
@is_admin
def toggle_user(id):
    editForm = forms.UserEditForm()
    if editForm.validate_on_submit():
        user = User.query.filter_by(id=id).first()
        if user.id == current_user.id:
            flash("Can't demote yourself!", "danger")
            return redirect(url_for("admin.users"))
        user.is_admin = not user.is_admin
        db.session.commit()
        flash("User status toggled!", "success")
    else:
        flash("Form couldn't validate!", "danger")

    return redirect(url_for("admin.users"))


@bp.route("/scope", methods=["GET", "POST"])
@login_required
@is_admin
def scope():
    scope = ScopeItem.getScope()
    scopeSize = current_app.ScopeManager.get_scope_size()

    # if it's zero, let's make sure the ScopeManager is up to date
    if scopeSize == 0:
        current_app.ScopeManager.update()
        scopeSize = current_app.ScopeManager.get_scope_size()
        # if it's zero again that's fine, we just had to check

    effectiveScopeSize = current_app.ScopeManager.get_effective_scope_size()

    newForm = forms.NewScopeForm()
    delForm = forms.ScopeDeleteForm()
    editForm = forms.ScopeToggleForm()
    importForm = forms.ImportScopeForm()
    addTagForm = forms.TagScopeForm()
    addTagForm.tagname.choices = [(row.name, row.name) for row in Tag.query.all()]
    if newForm.validate_on_submit():
        target = ipaddress.ip_network(newForm.target.data, False)
        newTarget = ScopeItem(target=target.with_prefixlen, blacklist=False)
        db.session.add(newTarget)
        db.session.commit()
        current_app.ScopeManager.update()
        flash(f"{newTarget.target} added!", "success")
        return redirect(url_for("admin.scope"))
    return render_template(
        "admin/scope.html",
        scope=scope,
        scopeSize=scopeSize,
        delForm=delForm,
        editForm=editForm,
        newForm=newForm,
        importForm=importForm,
        addTagForm=addTagForm,
        effectiveScopeSize=effectiveScopeSize,
    )


@bp.route("/blacklist", methods=["GET", "POST"])
@login_required
@is_admin
def blacklist():
    scope = ScopeItem.getBlacklist()
    blacklistSize = current_app.ScopeManager.get_blacklist_size()
    newForm = forms.NewScopeForm()
    delForm = forms.ScopeDeleteForm()
    editForm = forms.ScopeToggleForm()
    importForm = forms.ImportBlacklistForm()
    addTagForm = forms.TagScopeForm()
    addTagForm.tagname.choices = [(row.name, row.name) for row in Tag.query.all()]
    if newForm.validate_on_submit():
        target = ipaddress.ip_network(newForm.target.data, False)
        newTarget = ScopeItem(target=target.with_prefixlen, blacklist=True)
        db.session.add(newTarget)
        db.session.commit()
        current_app.ScopeManager.update()
        flash(f"{newTarget.target} blacklisted!", "success")
        return redirect(url_for("admin.blacklist"))
    return render_template(
        "admin/blacklist.html",
        scope=scope,
        blacklistSize=blacklistSize,
        delForm=delForm,
        editForm=editForm,
        newForm=newForm,
        importForm=importForm,
        addTagForm=addTagForm,
    )


@bp.route("/import/<string:scopetype>", methods=["POST"])
@login_required
@is_admin
def import_scope(scopetype=""):
    if scopetype == "blacklist":
        importBlacklist = True
        importForm = forms.ImportBlacklistForm()
    elif scopetype == "scope":
        importBlacklist = False
        importForm = forms.ImportScopeForm()
    else:
        return abort(404)
    if importForm.validate_on_submit():
        newScopeItems = importForm.scope.data.split("\n")
        fail, exist, success = ScopeItem.import_scope_list(
            newScopeItems, importBlacklist
        )
        db.session.commit()
        current_app.ScopeManager.update()
        if success:
            flash(f"{len(success)} targets added to {scopetype}!", "success")
        if exist:
            flash(f"{len(exist)} targets already existed!", "info")
        if fail:
            flash(f"{len(fail)} targets failed to import!", "danger")
            for item in fail:
                flash(f"{item}", "danger")
    else:
        for field, errors in importForm.errors.items():
            for error in errors:
                flash(error, "danger")
    return redirect(url_for(f"admin.{scopetype}"))


@bp.route("/export/<string:scopetype>", methods=["GET"])
@login_required
@is_admin
def export_scope(scopetype=""):
    if scopetype == "blacklist":
        exportBlacklist = True
    elif scopetype == "scope":
        exportBlacklist = False
    else:
        return abort(404)
    items = ScopeItem.query.filter_by(blacklist=exportBlacklist).all()
    return Response(
        "\n".join(str(item.target) for item in items), mimetype="text/plain"
    )


@bp.route("/<string:scopetype>/<int:id>/delete", methods=["POST"])
@login_required
@is_admin
def delete_scope(scopetype, id):
    if scopetype not in ["scope", "blacklist"]:
        return abort(404)
    delForm = forms.ScopeDeleteForm()
    if delForm.validate_on_submit():
        item = ScopeItem.query.filter_by(id=id).first()
        for tag in item.tags:
            item.tags.remove(tag)
        ScopeItem.query.filter_by(id=id).delete()
        db.session.commit()
        current_app.ScopeManager.update()
        flash(f"{item.target} deleted!", "success")
    else:
        flash("Form couldn't validate!", "danger")
    return redirects.get_scope_redirect(scopetype)


@bp.route("/<string:scopetype>/<int:id>/toggle", methods=["POST"])
@login_required
@is_admin
def toggle_scope(scopetype, id):
    if scopetype not in ["scope", "blacklist"]:
        return abort(404)
    toggleForm = forms.ScopeToggleForm()
    if toggleForm.validate_on_submit():
        item = ScopeItem.query.filter_by(id=id).first()
        item.blacklist = not item.blacklist
        flash(f"Toggled scope status for {item.target}!", "success")
        db.session.commit()
        current_app.ScopeManager.update()
    else:
        flash("Form couldn't validate!", "danger")
    return redirects.get_scope_redirect(scopetype)


@bp.route("/<string:scopetype>/<int:id>/tag", methods=["POST"])
@login_required
@is_admin
def tag_scope(scopetype, id):
    if scopetype not in ["scope", "blacklist"]:
        return abort(404)
    addTagForm = forms.TagScopeForm()
    addTagForm.tagname.choices = [(row.name, row.name) for row in Tag.query.all()]
    if addTagForm.validate_on_submit():
        scope = ScopeItem.query.get(id)
        mytag = Tag.query.filter_by(name=addTagForm.tagname.data).first()
        scope.addTag(mytag)
        db.session.commit()
        flash(f'Tag "{mytag.name}" added to {scope.target}', "success")
    else:
        flash("Form couldn't validate!", "danger")
    return redirects.get_scope_redirect(scopetype)


@bp.route("/<string:scopetype>/<int:id>/untag", methods=["POST"])
@login_required
@is_admin
def untag_scope(scopetype, id):
    if scopetype not in ["scope", "blacklist"]:
        return abort(404)
    delTagForm = forms.TagScopeForm()
    scope = ScopeItem.query.get(id)
    delTagForm.tagname.choices = [(row.name, row.name) for row in scope.tags]
    if delTagForm.validate_on_submit():
        mytag = Tag.query.filter_by(name=delTagForm.tagname.data).first()
        scope.delTag(mytag)
        db.session.commit()
        flash(f'Tag "{mytag.name}" removed from {scope.target}', "success")
    else:
        flash("Form couldn't validate!", "danger")
    return redirects.get_scope_redirect(scopetype)


@bp.route("/services", methods=["GET", "POST"])
@login_required
@is_admin
def services():
    uploadForm = forms.ServicesUploadForm(prefix="upload-services")
    addServiceForm = forms.AddServiceForm(prefix="add-service")
    addServiceForm.serviceProtocol.choices = [("tcp", "TCP"), ("udp", "UDP")]
    if uploadForm.uploadFile.data and uploadForm.validate_on_submit():
        newServicesContent = (
            uploadForm.serviceFile.data.read().decode("utf-8").rstrip("\r\n")
        )
        new_services = NatlasServices(services=newServicesContent)
        if not new_services.hash_equals(current_app.current_services["sha256"]):
            db.session.add(new_services)
            db.session.commit()
            current_app.current_services = new_services.as_dict()
            flash(
                f'New services file with hash {current_app.current_services["sha256"]} has been uploaded.',
                "success",
            )
        else:
            flash(
                "That file is an exact match for our current services file!", "warning"
            )
        return redirect(url_for("admin.services"))

    if addServiceForm.serviceName.data and addServiceForm.validate_on_submit():
        newServiceName = addServiceForm.serviceName.data
        newServicePort = (
            str(addServiceForm.servicePort.data)
            + "/"
            + addServiceForm.serviceProtocol.data
        )
        if "\t" + newServicePort in str(current_app.current_services["services"]):
            flash(f"A service with port {newServicePort} already exists!", "danger")
        else:
            newServices = (
                current_app.current_services["services"]
                + "\n"
                + newServiceName
                + "\t"
                + newServicePort
            )
            ns = NatlasServices(services=newServices)
            db.session.add(ns)
            db.session.commit()
            current_app.current_services = (
                NatlasServices.query.order_by(NatlasServices.id.desc())
                .first()
                .as_dict()
            )
            flash(
                f"New service {newServiceName} on port {newServicePort} has been added.",
                "success",
            )
        return redirect(url_for("admin.services"))

    return render_template(
        "admin/services.html",
        uploadForm=uploadForm,
        addServiceForm=addServiceForm,
        current_services=current_app.current_services,
        servlist=current_app.current_services["as_list"],
    )


@bp.route("/services/export", methods=["GET"])
@login_required
@is_admin
def export_services():
    return Response(
        str(current_app.current_services["services"]), mimetype="text/plain"
    )


@bp.route("/agents", methods=["GET", "POST"])
@login_required
@is_admin
def agent_config():
    agentConfig = AgentConfig.query.get(1)
    # pass the model to the form to populate
    agentForm = forms.AgentConfigForm(obj=agentConfig)
    addScriptForm = forms.AddScriptForm(prefix="add-script")
    delScriptForm = forms.DeleteForm(prefix="del-script")

    if agentForm.validate_on_submit():
        # populate the object from the form data
        agentForm.populate_obj(agentConfig)
        db.session.commit()
        current_app.agentConfig = agentConfig.as_dict()

    return render_template(
        "admin/agents.html",
        agentForm=agentForm,
        scripts=current_app.agentScripts,
        addScriptForm=addScriptForm,
        delScriptForm=delScriptForm,
    )


@bp.route("/agents/script/add", methods=["POST"])
@login_required
@is_admin
def add_script():
    addScriptForm = forms.AddScriptForm(prefix="add-script")

    if addScriptForm.validate_on_submit():
        newscript = AgentScript(name=addScriptForm.scriptName.data)
        db.session.add(newscript)
        db.session.commit()
        current_app.agentScripts = AgentScript.query.all()
        current_app.agentScriptStr = AgentScript.getScriptsString(
            current_app.agentScripts
        )
        flash(f"{newscript.name} successfully added to scripts", "success")
    else:
        flash(f"{addScriptForm.scriptName.data} couldn't be added to scripts", "danger")

    return redirect(url_for("admin.agent_config"))


@bp.route("/agents/script/<string:name>/delete", methods=["POST"])
@login_required
@is_admin
def delete_script(name):
    deleteForm = forms.DeleteForm()

    if deleteForm.validate_on_submit():
        delScript = AgentScript.query.filter_by(name=name).first()
        if delScript:
            db.session.delete(delScript)
            db.session.commit()
            current_app.agentScripts = AgentScript.query.all()
            current_app.agentScriptStr = AgentScript.getScriptsString(
                current_app.agentScripts
            )
            flash(f"{name} successfully deleted.", "success")
        else:
            flash(f"{name} doesn't exist", "danger")
        return redirect(url_for("admin.agent_config"))


@bp.route("/scans/delete/<scan_id>", methods=["POST"])
@login_required
@is_admin
def delete_scan(scan_id):
    delForm = forms.DeleteForm()
    redirectLoc = url_for("main.browse")

    if delForm.validate_on_submit():
        deleted = current_app.elastic.delete_scan(scan_id)
        if deleted not in [1, 2]:
            flash(f"Couldn't delete scan {scan_id}", "danger")
        else:
            flash(f"Successfully deleted scan {scan_id}.", "success")
    else:
        flash("Couldn't validate form!")

    return redirect(redirectLoc)


@bp.route("/hosts/delete/<ip>", methods=["POST"])
@login_required
@is_admin
def delete_host(ip):
    delForm = forms.DeleteForm()
    redirectLoc = url_for("main.browse")

    if delForm.validate_on_submit():
        deleted = current_app.elastic.delete_host(ip)
        if deleted > 0:
            flash(
                f"Successfully deleted {deleted - 1 if deleted > 1 else deleted} scans for {ip}",
                "success",
            )
            return redirect(redirectLoc)
        else:
            flash(f"Couldn't delete host: {ip}", "danger")
    else:
        flash("Couldn't validate form!")
        return redirect(redirectLoc)


@bp.route("/tags", methods=["GET", "POST"])
@login_required
@is_admin
def tags():
    tags = Tag.query.all()

    addForm = forms.AddTagForm()
    if addForm.validate_on_submit():
        prepared_tag = addForm.tagname.data.strip()
        newTag = Tag(name=prepared_tag)
        db.session.add(newTag)
        db.session.commit()
        flash(f"Successfully added tag {newTag.name}", "success")
        return redirect(url_for("admin.tags"))
    return render_template("admin/tags.html", tags=tags, addForm=addForm)


@bp.route("/logs", methods=["GET"])
@login_required
@is_admin
def logs():
    scope_logs = ScopeLog.query.order_by(ScopeLog.created_at.desc()).all()
    return render_template("admin/logs.html", scope_logs=scope_logs)
