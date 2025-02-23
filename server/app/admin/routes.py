import ipaddress
from typing import cast

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
from sqlalchemy import select
from werkzeug.wrappers.response import Response as wzResponse

from app import db, elastic, scope_manager
from app.admin import bp, forms, redirects
from app.auth.wrappers import is_admin
from app.models import (
    AgentConfig,
    NatlasServices,
    ScopeItem,
    ScopeLog,
    Tag,
    User,
    UserInvitation,
)


@bp.route("/", methods=["GET"])
@login_required  # type: ignore[misc]
@is_admin
def admin() -> str:
    configForm = forms.ConfigForm()
    configItems = current_app.config
    return render_template(
        "admin/index.html", configForm=configForm, configItems=configItems
    )


@bp.route("/users", methods=["GET", "POST"])
@login_required  # type: ignore[misc]
@is_admin
def users() -> Response | str:
    users = db.session.scalars(select(User)).all()
    inviteForm = forms.InviteUserForm()
    if inviteForm.validate_on_submit():
        emailaddr = cast(
            str, inviteForm.email.data
        )  # inviteForm requires this field and requires it to be a valid email
        invitation = UserInvitation.new_invite(emailaddr)
        msg = UserInvitation.deliver_invite(invitation)
        flash(msg, "success")
        db.session.commit()
        return redirect(url_for("admin.users"))  # type: ignore[return-value]
    return render_template(
        "admin/users.html",
        users=users,
        delForm=forms.UserDeleteForm(),
        editForm=forms.UserEditForm(),
        inviteForm=inviteForm,
    )


@bp.route("/users/<int:id>/delete", methods=["POST"])
@login_required  # type: ignore[misc]
@is_admin
def delete_user(id: int) -> wzResponse:
    delForm = forms.UserDeleteForm()
    if delForm.validate_on_submit():
        user = db.session.scalars(select(User).where(User.id == id)).first()
        if current_user.id == id:
            flash("You can't delete yourself!", "danger")
            return redirect(url_for("admin.users"))
        db.session.delete(db.session.get(User, id))
        db.session.commit()
        flash(f"{user.email} deleted.", "success")  # type: ignore[union-attr]
    else:
        flash("Form couldn't validate!", "danger")

    return redirect(url_for("admin.users"))


@bp.route("/users/<int:id>/toggle", methods=["POST"])
@login_required  # type: ignore[misc]
@is_admin
def toggle_user(id: int) -> wzResponse:
    editForm = forms.UserEditForm()
    if editForm.validate_on_submit():
        user = db.session.scalars(select(User).where(User.id == id)).first()
        if user.id == current_user.id:  # type: ignore[union-attr]
            flash("Can't demote yourself!", "danger")
            return redirect(url_for("admin.users"))
        user.is_admin = not user.is_admin  # type: ignore[union-attr]
        db.session.commit()
        flash("User status toggled.", "success")
    else:
        flash("Form couldn't validate!", "danger")

    return redirect(url_for("admin.users"))


@bp.route("/scope", methods=["GET", "POST"])
@login_required  # type: ignore[misc]
@is_admin
def scope() -> wzResponse | str:
    render = {
        "scope": ScopeItem.getScope(),
        "scopeSize": scope_manager.get_scope_size(),
        "effectiveScopeSize": scope_manager.get_effective_scope_size(),
        "newForm": forms.NewScopeForm(),
        "delForm": forms.ScopeDeleteForm(),
        "editForm": forms.ScopeToggleForm(),
        "importForm": forms.ImportScopeForm(),
        "addTagForm": forms.TagScopeForm(),
    }

    render["addTagForm"].tagname.choices = [  # type: ignore[attr-defined]
        (row.name, row.name) for row in db.session.scalars(select(Tag)).all()
    ]
    if render["newForm"].validate_on_submit():  # type: ignore[attr-defined]
        target = ipaddress.ip_network(render["newForm"].target.data, False)  # type: ignore[attr-defined]
        newTarget = ScopeItem(target=target.with_prefixlen, blacklist=False)
        db.session.add(newTarget)
        db.session.commit()
        scope_manager.update()
        flash(f"{newTarget.target} added.", "success")
        return redirect(url_for("admin.scope"))
    return render_template("admin/scope.html", **render)


@bp.route("/blacklist", methods=["GET", "POST"])
@login_required  # type: ignore[misc]
@is_admin
def blacklist() -> wzResponse | str:
    render = {
        "scope": ScopeItem.getBlacklist(),
        "blacklistSize": scope_manager.get_blacklist_size(),
        "effectiveScopeSize": scope_manager.get_effective_scope_size(),
        "newForm": forms.NewScopeForm(),
        "delForm": forms.ScopeDeleteForm(),
        "editForm": forms.ScopeToggleForm(),
        "importForm": forms.ImportScopeForm(),
        "addTagForm": forms.TagScopeForm(),
    }
    render["addTagForm"].tagname.choices = [  # type: ignore[attr-defined]
        (row.name, row.name) for row in db.session.scalars(select(Tag)).all()
    ]
    if render["newForm"].validate_on_submit():  # type: ignore[attr-defined]
        target = ipaddress.ip_network(render["newForm"].target.data, False)  # type: ignore[attr-defined]
        newTarget = ScopeItem(target=target.with_prefixlen, blacklist=True)
        db.session.add(newTarget)
        db.session.commit()
        scope_manager.update()
        flash(f"{newTarget.target} blacklisted.", "success")
        return redirect(url_for("admin.blacklist"))
    return render_template("admin/blacklist.html", **render)


@bp.route("/import/<string:scopetype>", methods=["POST"])
@login_required  # type: ignore[misc]
@is_admin
def import_scope(scopetype: str = "") -> wzResponse:
    if scopetype == "blacklist":
        importBlacklist = True
        importForm = forms.ImportBlacklistForm()
    elif scopetype == "scope":
        importBlacklist = False
        importForm = forms.ImportScopeForm()
    else:
        abort(404)
    if importForm.validate_on_submit():
        newScopeItems = importForm.scope.data.split("\n")
        result = ScopeItem.import_scope_list(newScopeItems, importBlacklist)
        db.session.commit()
        scope_manager.update()
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
@login_required  # type: ignore[misc]
@is_admin
def export_scope(scopetype: str = "") -> Response:
    if scopetype == "blacklist":
        exportBlacklist = True
    elif scopetype == "scope":
        exportBlacklist = False
    else:
        return abort(404)
    items = db.session.scalars(
        select(ScopeItem).where(ScopeItem.blacklist == exportBlacklist)
    ).all()
    return Response(
        "\n".join(str(item.target) for item in items), mimetype="text/plain"
    )


@bp.route("/<string:scopetype>/<int:id>/delete", methods=["POST"])
@login_required  # type: ignore[misc]
@is_admin
def delete_scope(scopetype: str, id: int) -> wzResponse:
    if scopetype not in ["scope", "blacklist"]:
        abort(404)
    delForm = forms.ScopeDeleteForm()
    if delForm.validate_on_submit():
        item = db.session.scalars(select(ScopeItem).where(ScopeItem.id == id)).first()
        for tag in item.tags:  # type: ignore[union-attr]
            item.tags.remove(tag)  # type: ignore[union-attr]
        db.session.delete(db.session.get(ScopeItem, id))
        db.session.commit()
        scope_manager.update()
        flash(f"{item.target} deleted.", "success")  # type: ignore[union-attr]
    else:
        flash("Form couldn't validate!", "danger")
    return redirects.get_scope_redirect(scopetype)


@bp.route("/<string:scopetype>/<int:id>/toggle", methods=["POST"])
@login_required  # type: ignore[misc]
@is_admin
def toggle_scope(scopetype: str, id: int) -> wzResponse:
    if scopetype not in ["scope", "blacklist"]:
        abort(404)
    toggleForm = forms.ScopeToggleForm()
    if toggleForm.validate_on_submit():
        item = db.session.scalars(select(ScopeItem).where(ScopeItem.id == id)).first()
        item.blacklist = not item.blacklist  # type: ignore[union-attr]
        flash(f"Toggled scope status for {item.target}.", "success")  # type: ignore[union-attr]
        db.session.commit()
        scope_manager.update()
    else:
        flash("Form couldn't validate!", "danger")
    return redirects.get_scope_redirect(scopetype)


@bp.route("/<string:scopetype>/<int:id>/tag", methods=["POST"])
@login_required  # type: ignore[misc]
@is_admin
def tag_scope(scopetype: str, id: int) -> wzResponse:
    if scopetype not in ["scope", "blacklist"]:
        abort(404)
    addTagForm = forms.TagScopeForm()
    addTagForm.tagname.choices = [
        (row.name, row.name) for row in db.session.scalars(select(Tag)).all()
    ]
    if addTagForm.validate_on_submit():
        scope = db.session.scalar(select(ScopeItem).where(ScopeItem.id == id))
        mytag = db.session.scalars(
            select(Tag).where(Tag.name == addTagForm.tagname.data)
        ).first()
        scope.addTag(mytag)  # type: ignore[union-attr, arg-type]
        db.session.commit()
        flash(f'Tag "{mytag.name}" added to {scope.target}.', "success")  # type: ignore[union-attr]
    else:
        flash("Form couldn't validate!", "danger")
    return redirects.get_scope_redirect(scopetype)


@bp.route("/<string:scopetype>/<int:id>/untag", methods=["POST"])
@login_required  # type: ignore[misc]
@is_admin
def untag_scope(scopetype: str, id: int) -> wzResponse:
    if scopetype not in ["scope", "blacklist"]:
        abort(404)
    delTagForm = forms.TagScopeForm()
    scope = db.session.get(ScopeItem, id)
    delTagForm.tagname.choices = [(row.name, row.name) for row in scope.tags]  # type: ignore[union-attr]
    if delTagForm.validate_on_submit():
        mytag = db.session.scalars(
            select(Tag).where(Tag.name == delTagForm.tagname.data)
        ).first()
        scope.delTag(mytag)  # type: ignore[union-attr, arg-type]
        db.session.commit()
        flash(f'Tag "{mytag.name}" removed from {scope.target}.', "success")  # type: ignore[union-attr]
    else:
        flash("Form couldn't validate!", "danger")
    return redirects.get_scope_redirect(scopetype)


@bp.route("/services", methods=["GET", "POST"])
@login_required  # type: ignore[misc]
@is_admin
def services() -> wzResponse | str:
    uploadForm = forms.ServicesUploadForm(prefix="upload-services")
    addServiceForm = forms.AddServiceForm(prefix="add-service")
    addServiceForm.serviceProtocol.choices = [("tcp", "TCP"), ("udp", "UDP")]
    services = db.session.get(NatlasServices, 1)

    if uploadForm.uploadFile.data and uploadForm.validate_on_submit():
        newServicesContent = (
            uploadForm.serviceFile.data.read().decode("utf-8").rstrip("\r\n")
        )
        if not services:
            services = NatlasServices(services=newServicesContent)
            db.session.add(services)
            db.session.commit()
        else:
            services.update_services(newServicesContent)
            db.session.commit()
        flash("Natlas Services Updated", "success")
        return redirect(url_for("admin.services"))

    if addServiceForm.serviceName.data and addServiceForm.validate_on_submit():
        newServiceName = addServiceForm.serviceName.data
        newServicePort = (
            str(addServiceForm.servicePort.data)
            + "/"
            + addServiceForm.serviceProtocol.data
        )
        newServiceLine = f"{newServiceName}\t{newServicePort}"
        if not services:
            services = NatlasServices(services=newServiceLine)
            db.session.add(services)
            db.session.commit()
        elif "\t" + newServicePort in services.services:
            flash(f"A service with port {newServicePort} already exists!", "danger")
        else:
            newServices = f"{services.services}\n{newServiceLine}"
            services.update_services(newServices)
            db.session.commit()
            flash(
                f"New service {newServiceName} on port {newServicePort} has been added.",
                "success",
            )
        return redirect(url_for("admin.services"))

    return render_template(
        "admin/services.html",
        uploadForm=uploadForm,
        addServiceForm=addServiceForm,
        current_services=services,
        servlist=services.services_as_list(),
    )


@bp.route("/services/export", methods=["GET"])
@login_required  # type: ignore[misc]
@is_admin
def export_services() -> Response:
    services = db.session.get(NatlasServices, 1)
    if not services:
        return Response("No services found", status=400)
    return Response(str(services.services), mimetype="text/plain")


@bp.route("/agents", methods=["GET", "POST"])
@login_required  # type: ignore[misc]
@is_admin
def agent_config() -> str:
    agentConfig = db.session.get(AgentConfig, 1)
    # pass the model to the form to populate
    agentForm = forms.AgentConfigForm(obj=agentConfig)
    addScriptForm = forms.AddScriptForm(prefix="add-script")
    delScriptForm = forms.DeleteForm(prefix="del-script")

    if agentForm.validate_on_submit():
        # populate the object from the form data
        agentForm.populate_obj(agentConfig)
        db.session.commit()
        flash("Successfully updated agent configuration.", "success")

    return render_template(
        "admin/agents.html",
        agentForm=agentForm,
        scripts=agentConfig.scripts,
        addScriptForm=addScriptForm,
        delScriptForm=delScriptForm,
    )


@bp.route("/agents/script/add", methods=["POST"])
@login_required  # type: ignore[misc]
@is_admin
def add_script() -> wzResponse:
    addScriptForm = forms.AddScriptForm(prefix="add-script")

    if addScriptForm.validate_on_submit():
        script_name = addScriptForm.scriptName.data
        config = db.session.get(AgentConfig, 1)
        config.scripts.append(script_name)
        db.session.add(config)
        db.session.commit()
        flash(f"{script_name} successfully added to scripts.", "success")
    else:
        flash(
            f"{addScriptForm.scriptName.data} couldn't be added to scripts!", "danger"
        )

    return redirect(url_for("admin.agent_config"))


@bp.route("/agents/script/<string:name>/delete", methods=["POST"])
@login_required  # type: ignore[misc]
@is_admin
def delete_script(name: str) -> wzResponse | None:
    deleteForm = forms.DeleteForm()

    if deleteForm.validate_on_submit():
        config = db.session.get(AgentConfig, 1)

        if name in config.scripts:
            config.scripts.remove(name)
            db.session.add(config)
            db.session.commit()
            flash(f"{name} successfully deleted.", "success")
        else:
            flash(f"{name} doesn't exist!", "danger")
        return redirect(url_for("admin.agent_config"))
    return None


@bp.route("/scans/delete/<scan_id>", methods=["POST"])
@login_required  # type: ignore[misc]
@is_admin
def delete_scan(scan_id: str) -> wzResponse:
    delForm = forms.DeleteForm()
    redirectLoc = url_for("main.browse")

    if delForm.validate_on_submit():
        deleted = elastic.delete_scan(scan_id)
        if deleted not in [1, 2]:
            flash(f"Couldn't delete scan {scan_id}!", "danger")
        else:
            flash(f"Successfully deleted scan {scan_id}.", "success")
    else:
        flash("Couldn't validate form!")

    return redirect(redirectLoc)


@bp.route("/hosts/delete/<ip>", methods=["POST"])
@login_required  # type: ignore[misc]
@is_admin
def delete_host(ip: str) -> wzResponse | None:
    delForm = forms.DeleteForm()
    redirectLoc = url_for("main.browse")

    if delForm.validate_on_submit():
        deleted = elastic.delete_host(ip)
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
@login_required  # type: ignore[misc]
@is_admin
def tags() -> str | wzResponse:
    tags = db.session.scalars(select(Tag)).all()

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
@login_required  # type: ignore[misc]
@is_admin
def logs() -> str:
    scope_logs = db.session.scalars(
        select(ScopeLog).order_by(ScopeLog.created_at.desc())
    ).all()
    return render_template("admin/logs.html", scope_logs=scope_logs)
