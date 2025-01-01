import ipaddress

from flask import (
    Response,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.admin import bp, forms, redirects
from app.auth.wrappers import is_admin
from app.models import (
    AgentConfig,
    AgentScript,
    ConfigItem,
    NatlasServices,
    ScopeItem,
    ScopeLog,
    Tag,
    User,
    UserInvitation,
)


@bp.route("/", methods=["GET", "POST"])
@login_required
@is_admin
def admin():  # type: ignore[no-untyped-def]
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
        flash("Successfully updated Natlas configuration.", "success")
    return render_template(
        "admin/index.html", configForm=configForm, configItems=configItems
    )


@bp.route("/users", methods=["GET", "POST"])
@login_required
@is_admin
def users():  # type: ignore[no-untyped-def]
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
def delete_user(id):  # type: ignore[no-untyped-def]
    delForm = forms.UserDeleteForm()
    if delForm.validate_on_submit():
        if current_user.id == id:
            flash("You can't delete yourself!", "danger")
            return redirect(url_for("admin.users"))
        user = User.query.filter_by(id=id).first()
        User.query.filter_by(id=id).delete()
        db.session.commit()
        flash(f"{user.email} deleted.", "success")
    else:
        flash("Form couldn't validate!", "danger")

    return redirect(url_for("admin.users"))


@bp.route("/users/<int:id>/toggle", methods=["POST"])
@login_required
@is_admin
def toggle_user(id):  # type: ignore[no-untyped-def]
    editForm = forms.UserEditForm()
    if editForm.validate_on_submit():
        user = User.query.filter_by(id=id).first()
        if user.id == current_user.id:
            flash("Can't demote yourself!", "danger")
            return redirect(url_for("admin.users"))
        user.is_admin = not user.is_admin
        db.session.commit()
        flash("User status toggled.", "success")
    else:
        flash("Form couldn't validate!", "danger")

    return redirect(url_for("admin.users"))


@bp.route("/scope", methods=["GET", "POST"])
@login_required
@is_admin
def scope():  # type: ignore[no-untyped-def]
    render = {
        "scope": ScopeItem.getScope(),
        "scopeSize": current_app.ScopeManager.get_scope_size(),  # type: ignore[attr-defined]
        "effectiveScopeSize": current_app.ScopeManager.get_effective_scope_size(),  # type: ignore[attr-defined]
        "newForm": forms.NewScopeForm(),
        "delForm": forms.ScopeDeleteForm(),
        "editForm": forms.ScopeToggleForm(),
        "importForm": forms.ImportScopeForm(),
        "addTagForm": forms.TagScopeForm(),
    }

    render["addTagForm"].tagname.choices = [
        (row.name, row.name) for row in Tag.query.all()
    ]
    if render["newForm"].validate_on_submit():
        target = ipaddress.ip_network(render["newForm"].target.data, False)
        newTarget = ScopeItem(target=target.with_prefixlen, blacklist=False)
        db.session.add(newTarget)
        db.session.commit()
        current_app.ScopeManager.update()  # type: ignore[attr-defined]
        flash(f"{newTarget.target} added.", "success")
        return redirect(url_for("admin.scope"))
    return render_template("admin/scope.html", **render)


@bp.route("/blacklist", methods=["GET", "POST"])
@login_required
@is_admin
def blacklist():  # type: ignore[no-untyped-def]
    render = {
        "scope": ScopeItem.getBlacklist(),
        "blacklistSize": current_app.ScopeManager.get_blacklist_size(),  # type: ignore[attr-defined]
        "effectiveScopeSize": current_app.ScopeManager.get_effective_scope_size(),  # type: ignore[attr-defined]
        "newForm": forms.NewScopeForm(),
        "delForm": forms.ScopeDeleteForm(),
        "editForm": forms.ScopeToggleForm(),
        "importForm": forms.ImportScopeForm(),
        "addTagForm": forms.TagScopeForm(),
    }
    render["addTagForm"].tagname.choices = [
        (row.name, row.name) for row in Tag.query.all()
    ]
    if render["newForm"].validate_on_submit():
        target = ipaddress.ip_network(render["newForm"].target.data, False)
        newTarget = ScopeItem(target=target.with_prefixlen, blacklist=True)
        db.session.add(newTarget)
        db.session.commit()
        current_app.ScopeManager.update()  # type: ignore[attr-defined]
        flash(f"{newTarget.target} blacklisted.", "success")
        return redirect(url_for("admin.blacklist"))
    return render_template("admin/blacklist.html", **render)


@bp.route("/import/<string:scopetype>", methods=["POST"])
@login_required
@is_admin
def import_scope(scopetype=""):  # type: ignore[no-untyped-def]
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
        result = ScopeItem.import_scope_list(newScopeItems, importBlacklist)
        db.session.commit()
        current_app.ScopeManager.update()  # type: ignore[attr-defined]
        if result["success"]:
            flash(f"{result['success']} targets added to {scopetype}.", "success")
        if result["exist"]:
            flash(f"{result['exist']} targets already existed.", "info")
        if result["fail"]:
            flash(f"{len(result['fail'])} targets failed to import!", "danger")
            for item in result["fail"]:
                flash(f"{item}", "danger")
    else:
        for _field, errors in importForm.errors.items():
            for error in errors:
                flash(error, "danger")
    return redirect(url_for(f"admin.{scopetype}"))


@bp.route("/export/<string:scopetype>", methods=["GET"])
@login_required
@is_admin
def export_scope(scopetype=""):  # type: ignore[no-untyped-def]
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
def delete_scope(scopetype, id):  # type: ignore[no-untyped-def]
    if scopetype not in ["scope", "blacklist"]:
        return abort(404)
    delForm = forms.ScopeDeleteForm()
    if delForm.validate_on_submit():
        item = ScopeItem.query.filter_by(id=id).first()
        for tag in item.tags:
            item.tags.remove(tag)
        ScopeItem.query.filter_by(id=id).delete()
        db.session.commit()
        current_app.ScopeManager.update()  # type: ignore[attr-defined]
        flash(f"{item.target} deleted.", "success")
    else:
        flash("Form couldn't validate!", "danger")
    return redirects.get_scope_redirect(scopetype)


@bp.route("/<string:scopetype>/<int:id>/toggle", methods=["POST"])
@login_required
@is_admin
def toggle_scope(scopetype, id):  # type: ignore[no-untyped-def]
    if scopetype not in ["scope", "blacklist"]:
        return abort(404)
    toggleForm = forms.ScopeToggleForm()
    if toggleForm.validate_on_submit():
        item = ScopeItem.query.filter_by(id=id).first()
        item.blacklist = not item.blacklist
        flash(f"Toggled scope status for {item.target}.", "success")
        db.session.commit()
        current_app.ScopeManager.update()  # type: ignore[attr-defined]
    else:
        flash("Form couldn't validate!", "danger")
    return redirects.get_scope_redirect(scopetype)


@bp.route("/<string:scopetype>/<int:id>/tag", methods=["POST"])
@login_required
@is_admin
def tag_scope(scopetype, id):  # type: ignore[no-untyped-def]
    if scopetype not in ["scope", "blacklist"]:
        return abort(404)
    addTagForm = forms.TagScopeForm()
    addTagForm.tagname.choices = [(row.name, row.name) for row in Tag.query.all()]
    if addTagForm.validate_on_submit():
        scope = ScopeItem.query.get(id)
        mytag = Tag.query.filter_by(name=addTagForm.tagname.data).first()
        scope.addTag(mytag)
        db.session.commit()
        flash(f'Tag "{mytag.name}" added to {scope.target}.', "success")
    else:
        flash("Form couldn't validate!", "danger")
    return redirects.get_scope_redirect(scopetype)


@bp.route("/<string:scopetype>/<int:id>/untag", methods=["POST"])
@login_required
@is_admin
def untag_scope(scopetype, id):  # type: ignore[no-untyped-def]
    if scopetype not in ["scope", "blacklist"]:
        return abort(404)
    delTagForm = forms.TagScopeForm()
    scope = ScopeItem.query.get(id)
    delTagForm.tagname.choices = [(row.name, row.name) for row in scope.tags]
    if delTagForm.validate_on_submit():
        mytag = Tag.query.filter_by(name=delTagForm.tagname.data).first()
        scope.delTag(mytag)
        db.session.commit()
        flash(f'Tag "{mytag.name}" removed from {scope.target}.', "success")
    else:
        flash("Form couldn't validate!", "danger")
    return redirects.get_scope_redirect(scopetype)


@bp.route("/services", methods=["GET", "POST"])
@login_required
@is_admin
def services():  # type: ignore[no-untyped-def]
    uploadForm = forms.ServicesUploadForm(prefix="upload-services")
    addServiceForm = forms.AddServiceForm(prefix="add-service")
    addServiceForm.serviceProtocol.choices = [("tcp", "TCP"), ("udp", "UDP")]
    if uploadForm.uploadFile.data and uploadForm.validate_on_submit():
        newServicesContent = (
            uploadForm.serviceFile.data.read().decode("utf-8").rstrip("\r\n")
        )
        new_services = NatlasServices(services=newServicesContent)
        if not new_services.hash_equals(current_app.current_services["sha256"]):  # type: ignore[attr-defined]
            db.session.add(new_services)
            db.session.commit()
            current_app.current_services = new_services.as_dict()  # type: ignore[attr-defined]
            flash(
                f'New services file with hash {current_app.current_services["sha256"]} has been uploaded.',  # type: ignore[attr-defined]
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
        if "\t" + newServicePort in str(current_app.current_services["services"]):  # type: ignore[attr-defined]
            flash(f"A service with port {newServicePort} already exists!", "danger")
        else:
            newServices = (
                current_app.current_services["services"]  # type: ignore[attr-defined]
                + "\n"
                + newServiceName
                + "\t"
                + newServicePort
            )
            ns = NatlasServices(services=newServices)
            db.session.add(ns)
            db.session.commit()
            current_app.current_services = NatlasServices.get_latest_services()  # type: ignore[attr-defined]
            flash(
                f"New service {newServiceName} on port {newServicePort} has been added.",
                "success",
            )
        return redirect(url_for("admin.services"))

    current_services = NatlasServices.get_latest_services()
    return render_template(
        "admin/services.html",
        uploadForm=uploadForm,
        addServiceForm=addServiceForm,
        current_services=current_services,
        servlist=current_services["as_list"],
    )


@bp.route("/services/export", methods=["GET"])
@login_required
@is_admin
def export_services():  # type: ignore[no-untyped-def]
    current_services = NatlasServices.get_latest_services()
    return Response(str(current_services["services"]), mimetype="text/plain")


@bp.route("/agents", methods=["GET", "POST"])
@login_required
@is_admin
def agent_config():  # type: ignore[no-untyped-def]
    agentConfig = AgentConfig.query.get(1)
    agent_scripts = AgentScript.query.all()
    # pass the model to the form to populate
    agentForm = forms.AgentConfigForm(obj=agentConfig)
    addScriptForm = forms.AddScriptForm(prefix="add-script")
    delScriptForm = forms.DeleteForm(prefix="del-script")

    if agentForm.validate_on_submit():
        # populate the object from the form data
        agentForm.populate_obj(agentConfig)
        db.session.commit()
        current_app.agentConfig = agentConfig.as_dict()  # type: ignore[attr-defined]
        flash("Successfully updated agent configuration.", "success")

    return render_template(
        "admin/agents.html",
        agentForm=agentForm,
        scripts=agent_scripts,
        addScriptForm=addScriptForm,
        delScriptForm=delScriptForm,
    )


@bp.route("/agents/script/add", methods=["POST"])
@login_required
@is_admin
def add_script():  # type: ignore[no-untyped-def]
    addScriptForm = forms.AddScriptForm(prefix="add-script")

    if addScriptForm.validate_on_submit():
        newscript = AgentScript(name=addScriptForm.scriptName.data)
        db.session.add(newscript)
        db.session.commit()
        current_app.agent_scripts = AgentScript.get_scripts_string()  # type: ignore[attr-defined]
        flash(f"{newscript.name} successfully added to scripts.", "success")
    else:
        flash(
            f"{addScriptForm.scriptName.data} couldn't be added to scripts!", "danger"
        )

    return redirect(url_for("admin.agent_config"))


@bp.route("/agents/script/<string:name>/delete", methods=["POST"])
@login_required
@is_admin
def delete_script(name):  # type: ignore[no-untyped-def]
    deleteForm = forms.DeleteForm()

    if deleteForm.validate_on_submit():
        delScript = AgentScript.query.filter_by(name=name).first()
        if delScript:
            db.session.delete(delScript)
            db.session.commit()
            current_app.agent_scripts = AgentScript.get_scripts_string()  # type: ignore[attr-defined]
            flash(f"{name} successfully deleted.", "success")
        else:
            flash(f"{name} doesn't exist!", "danger")
        return redirect(url_for("admin.agent_config"))
    return None


@bp.route("/scans/delete/<scan_id>", methods=["POST"])
@login_required
@is_admin
def delete_scan(scan_id):  # type: ignore[no-untyped-def]
    delForm = forms.DeleteForm()
    redirectLoc = url_for("main.browse")

    if delForm.validate_on_submit():
        deleted = current_app.elastic.delete_scan(scan_id)  # type: ignore[attr-defined]
        if deleted not in [1, 2]:
            flash(f"Couldn't delete scan {scan_id}!", "danger")
        else:
            flash(f"Successfully deleted scan {scan_id}.", "success")
    else:
        flash("Couldn't validate form!")

    return redirect(redirectLoc)


@bp.route("/hosts/delete/<ip>", methods=["POST"])
@login_required
@is_admin
def delete_host(ip):  # type: ignore[no-untyped-def]
    delForm = forms.DeleteForm()
    redirectLoc = url_for("main.browse")

    if delForm.validate_on_submit():
        deleted = current_app.elastic.delete_host(ip)  # type: ignore[attr-defined]
        if deleted > 0:
            flash(
                f"Successfully deleted {deleted - 1 if deleted > 1 else deleted} scans for {ip}.",
                "success",
            )
            return redirect(redirectLoc)
        flash(f"Couldn't delete host: {ip}!", "danger")
        return None
    flash("Couldn't validate form!")
    return redirect(redirectLoc)


@bp.route("/tags", methods=["GET", "POST"])
@login_required
@is_admin
def tags():  # type: ignore[no-untyped-def]
    tags = Tag.query.all()

    addForm = forms.AddTagForm()
    if addForm.validate_on_submit():
        prepared_tag = addForm.tagname.data.strip()
        newTag = Tag(name=prepared_tag)
        db.session.add(newTag)
        db.session.commit()
        flash(f"Successfully added tag {newTag.name}.", "success")
        return redirect(url_for("admin.tags"))
    return render_template("admin/tags.html", tags=tags, addForm=addForm)


@bp.route("/logs", methods=["GET"])
@login_required
@is_admin
def logs():  # type: ignore[no-untyped-def]
    scope_logs = ScopeLog.query.order_by(ScopeLog.created_at.desc()).all()
    return render_template("admin/logs.html", scope_logs=scope_logs)
