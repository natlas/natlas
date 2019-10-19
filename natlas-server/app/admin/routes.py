from flask import render_template, redirect, url_for, current_app, flash, Response, abort, request
from flask_login import current_user
from app import db
from app.admin import bp
from app.elastic import Elastic
from app.admin.forms import *
from app.models import User, ScopeItem, ConfigItem, NatlasServices, AgentConfig, Tag
from app.auth.email import send_user_invite_email
from app.auth.wrappers import isAuthenticated, isAdmin
import ipaddress, hashlib

@bp.route('/', methods=['GET', 'POST'])
@isAuthenticated
@isAdmin
def admin():
	configForm = ConfigForm()
	configItems = current_app.config
	if configForm.validate_on_submit():
		for fieldname, fieldvalue in configForm.data.items():
			if fieldname.upper() in ["SUBMIT", "CSRF_TOKEN"]:
				continue
			if fieldname.upper() == "ELASTICSEARCH_URL" and fieldvalue != current_app.config["ELASTICSEARCH_URL"]: # if we've got a new elasticsearch address, update our current handle to elastic
				current_app.elastic = Elastic(fieldvalue)
			current_app.config[fieldname.upper()] = fieldvalue
			confitem = ConfigItem.query.filter_by(name=fieldname.upper()).first()
			confitem.value=str(fieldvalue)
			db.session.add(confitem)
		db.session.commit()
	return render_template("admin/index.html", configForm=configForm, configItems=configItems)


@bp.route('/users', methods=['GET', 'POST'])
@isAuthenticated
@isAdmin
def users():
	users = User.query.all()
	delForm = UserDeleteForm()
	editForm = UserEditForm()
	inviteForm = InviteUserForm()
	if inviteForm.validate_on_submit():
		validemail = User.validate_email(inviteForm.email.data)
		if not validemail:
			flash("%s does not appear to be a valid, deliverable email address." % inviteForm.email.data, "danger")
			return redirect(request.referrer)
		newUser = User(email=validemail)
		db.session.add(newUser)
		db.session.commit()
		send_user_invite_email(newUser)
		flash('Invitation Sent!', 'success')
		return redirect(url_for('admin.users'))
	return render_template("admin/users.html", users=users, delForm=delForm, editForm=editForm, inviteForm=inviteForm)


@bp.route('/users/<int:id>/delete', methods=['POST'])
@isAuthenticated
@isAdmin
def deleteUser(id):
	delForm = UserDeleteForm()
	if delForm.validate_on_submit():
		if current_user.id == id:
			flash('You can\'t delete yourself!', 'danger')
			return redirect(url_for('admin.users'))
		user = User.query.filter_by(id=id).first()
		User.query.filter_by(id=id).delete()
		db.session.commit()
		flash('%s deleted!' % user.email, 'success')
		return redirect(url_for('admin.users'))
	else:
		flash("Form couldn't validate!", 'danger')
		return redirect(url_for('admin.users'))


@bp.route('/users/<int:id>/toggle', methods=['POST'])
@isAuthenticated
@isAdmin
def toggleUser(id):
	editForm = UserEditForm()
	if editForm.validate_on_submit():
		user = User.query.filter_by(id=id).first()
		if user.is_admin:
			admins = User.query.filter_by(is_admin=True).all()
			if len(admins) == 1:
				flash('Can\'t delete the last admin!', 'danger')
				return redirect(url_for('admin.users'))
			user.is_admin = False
			db.session.commit()
			flash('User demoted!', 'success')
			return redirect(url_for('admin.users'))
		else:
			user.is_admin = True
			db.session.commit()
			flash('User promoted!', 'success')
			return redirect(url_for('admin.users'))
	else:
		flash("Form couldn't validate!", 'danger')
		return redirect(url_for('admin.users'))


@bp.route('/scope', methods=['GET', 'POST'])
@isAuthenticated
@isAdmin
def scope():
	scope = ScopeItem.getScope()
	scopeSize = current_app.ScopeManager.getScopeSize()
	if scopeSize == 0: # if it's zero, let's update the app's scopemanager
		current_app.ScopeManager.update()
		scopeSize = current_app.ScopeManager.getScopeSize() # if it's zero again that's fine, we just had to check
	newForm = NewScopeForm()
	delForm = ScopeDeleteForm()
	editForm = ScopeToggleForm()
	importForm = ImportScopeForm()
	addTagForm = TagScopeForm()
	addTagForm.tagname.choices = [(row.name, row.name) for row in Tag.query.all()]
	if newForm.validate_on_submit():
		if '/' not in newForm.target.data:
			newForm.target.data = newForm.target.data + '/32'
		target = ipaddress.ip_network(newForm.target.data, False)
		newTarget = ScopeItem(target=target.with_prefixlen, blacklist=False)
		db.session.add(newTarget)
		db.session.commit()
		current_app.ScopeManager.update()
		flash('%s added!' % newTarget.target, 'success')
		return redirect(url_for('admin.scope'))
	return render_template("admin/scope.html", scope=scope, scopeSize=scopeSize, delForm=delForm, editForm=editForm, newForm=newForm, importForm=importForm, \
		addTagForm=addTagForm)


@bp.route('/blacklist', methods=['GET', 'POST'])
@isAuthenticated
@isAdmin
def blacklist():
	scope = ScopeItem.getBlacklist()
	blacklistSize = current_app.ScopeManager.getBlacklistSize()
	newForm = NewScopeForm()
	delForm = ScopeDeleteForm()
	editForm = ScopeToggleForm()
	importForm = ImportBlacklistForm()
	if newForm.validate_on_submit():
		if '/' not in newForm.target.data:
			newForm.target.data = newForm.target.data + '/32'
		target = ipaddress.ip_network(newForm.target.data, False)
		newTarget = ScopeItem(target=target.with_prefixlen, blacklist=True)
		db.session.add(newTarget)
		db.session.commit()
		current_app.ScopeManager.update()
		flash('%s blacklisted!' % newTarget.target, 'success')
		return redirect(url_for('admin.blacklist'))
	return render_template("admin/blacklist.html", scope=scope, blacklistSize=blacklistSize, delForm=delForm, editForm=editForm, newForm=newForm, importForm=importForm)



@bp.route('/import/<string:scopetype>', methods=['POST'])
@isAuthenticated
@isAdmin
def importScope(scopetype=''):
	if scopetype == 'blacklist':
		importBlacklist = True
		importForm = ImportBlacklistForm()
	elif scopetype == 'scope':
		importBlacklist = False
		importForm = ImportScopeForm()
	else:
		abort(404)
	if importForm.validate_on_submit():
		successImports = []
		alreadyExists = []
		failedImports = []
		newScopeItems = importForm.scope.data.split('\n')
		for item in newScopeItems:
			item = item.strip()
			fail, exist, success = ScopeItem.importScope(item, importBlacklist)
			failedImports = failedImports + fail
			alreadyExists = alreadyExists + exist
			successImports = successImports + success
		db.session.commit()
		current_app.ScopeManager.update()
		if len(successImports) > 0:
			flash('%s targets added to %s!' % (len(successImports), scopetype), 'success')
		if len(alreadyExists) > 0:
			flash('%s targets already existed!' % len(alreadyExists), 'info')
		if len(failedImports) > 0:
			flash('%s targets failed to import!' % len(failedImports), 'danger')
			for item in failedImport:
				flash('%s' % item, 'danger')
		return redirect(url_for('admin.%s' % scopetype))
	else:
		for field, errors in importForm.errors.items():
			for error in errors:
				flash(error, 'danger')
		return redirect(url_for('admin.%s' % scopetype))

@bp.route('/export/<string:scopetype>', methods=['GET'])
@isAuthenticated
@isAdmin
def exportScope(scopetype=''):
	if scopetype == 'blacklist':
		exportBlacklist = True
	elif scopetype == 'scope':
		exportBlacklist = False
	else:
		abort(404)
	items = ScopeItem.query.filter_by(blacklist=exportBlacklist).all()
	return Response('\n'.join(str(item.target) for item in items), mimetype='text/plain')

@bp.route('/scope/<int:id>/delete', methods=['POST'])
@isAuthenticated
@isAdmin
def deleteScopeItem(id):
	delForm = ScopeDeleteForm()
	if delForm.validate_on_submit():
		item = ScopeItem.query.filter_by(id=id).first()
		for tag in item.tags:
			item.tags.remove(tag)
		ScopeItem.query.filter_by(id=id).delete()
		db.session.commit()
		current_app.ScopeManager.update()
		flash('%s deleted!' % item.target, 'success')
		return redirect(request.referrer)
	else:
		flash("Form couldn't validate!", 'danger')
		return redirect(request.referrer)


@bp.route('/scope/<int:id>/toggle', methods=['POST'])
@isAuthenticated
@isAdmin
def toggleScopeItem(id):
	toggleForm = ScopeToggleForm()
	if toggleForm.validate_on_submit():
		item = ScopeItem.query.filter_by(id=id).first()
		if item.blacklist:
			item.blacklist = False
			flash('%s removed from blacklist!' % item.target, 'success')
		else:
			item.blacklist = True
			flash('%s blacklisted!' % item.target, 'success')
		db.session.commit()
		current_app.ScopeManager.update()
		return redirect(request.referrer)
	else:
		flash("Form couldn't validate!", 'danger')
		return redirect(request.referrer)

@bp.route('/scope/<int:id>/tag', methods=['POST'])
@isAuthenticated
@isAdmin
def tagScopeItem(id):
	addTagForm = TagScopeForm()
	addTagForm.tagname.choices = [(row.name, row.name) for row in Tag.query.all()]
	if addTagForm.validate_on_submit():
		scope = ScopeItem.query.get(id)
		mytag = Tag.query.filter_by(name=addTagForm.tagname.data).first()
		scope.addTag(mytag)
		db.session.commit()
		flash("Tag \"%s\" added to %s" % (mytag.name, scope.target), "success")
		return redirect(request.referrer)
	else:
		flash("Form couldn't validate!", 'danger')
		return redirect(request.referrer)

@bp.route('/scope/<int:id>/untag', methods=['POST'])
@isAuthenticated
@isAdmin
def untagScopeItem(id):
	delTagForm = TagScopeForm()
	scope = ScopeItem.query.get(id)
	delTagForm.tagname.choices = [(row.name, row.name) for row in scope.tags.all()]
	if delTagForm.validate_on_submit():
		mytag = Tag.query.filter_by(name=delTagForm.tagname.data).first()
		scope.delTag(mytag)
		db.session.commit()
		flash("Tag \"%s\" removed from %s" % (mytag.name, scope.target), "success")
		return redirect(request.referrer)
	else:
		flash("Form couldn't validate!", 'danger')
		return redirect(request.referrer)

@bp.route('/services', methods=['GET', 'POST'])
@isAuthenticated
@isAdmin
def services():
	uploadForm = ServicesUploadForm(prefix="upload-services")
	addServiceForm = AddServiceForm(prefix="add-service")
	addServiceForm.serviceProtocol.choices = [("tcp", "TCP"), ("udp","UDP")]
	if uploadForm.uploadFile.data and uploadForm.validate_on_submit():
		newServicesContent = uploadForm.serviceFile.data.read().decode("utf-8").rstrip('\r\n')
		newServicesSha = hashlib.sha256(newServicesContent.encode()).hexdigest()
		if newServicesSha != current_app.current_services["sha256"]:
			ns = NatlasServices(sha256=newServicesSha, services=newServicesContent)
			db.session.add(ns)
			db.session.commit()
			current_app.current_services = NatlasServices.query.order_by(NatlasServices.id.desc()).first().as_dict()
			flash("New services file with hash %s has been uploaded." % current_app.current_services["sha256"], "success")
			return redirect(url_for('admin.services'))
		else:
			flash("That file is an exact match for our current services file!", "warning")
			return redirect(url_for('admin.services'))

	if addServiceForm.serviceName.data and addServiceForm.validate_on_submit():
		newServiceName = addServiceForm.serviceName.data
		newServicePort = str(addServiceForm.servicePort.data) + '/' + addServiceForm.serviceProtocol.data
		if '\t' + newServicePort in str(current_app.current_services['services']):
			flash("A service with port %s already exists!" % newServicePort, "danger")
			return redirect(url_for('admin.services'))
		else:
			newServices = current_app.current_services["services"] + "\n" + newServiceName + "\t" + newServicePort
			newSha = hashlib.sha256(newServices.encode()).hexdigest()
			ns = NatlasServices(sha256=newSha, services=newServices)
			db.session.add(ns)
			db.session.commit()
			current_app.current_services = NatlasServices.query.order_by(NatlasServices.id.desc()).first().as_dict()
			flash("New service %s on port %s has been added." % (newServiceName, newServicePort), "success")
			return redirect(url_for('admin.services'))


	return render_template('admin/services.html', uploadForm=uploadForm, addServiceForm=addServiceForm, current_services=current_app.current_services, servlist=current_app.current_services['as_list'])

@bp.route('/services/export', methods=['GET'])
@isAuthenticated
@isAdmin
def exportServices():
	return Response(str(current_app.current_services["services"]), mimetype='text/plain')

@bp.route('/agents', methods=['GET', 'POST'])
@isAuthenticated
@isAdmin
def agentConfig():
	agentConfig = AgentConfig.query.get(1)
	agentForm = AgentConfigForm(obj=agentConfig) # pass the model to the form to populate
	addScriptForm = AddScriptForm(prefix="add-script")
	delScriptForm = DeleteForm(prefix="del-script")

	if agentForm.validate_on_submit():
		agentForm.populate_obj(agentConfig) # populate the object from the form data
		db.session.commit()
		current_app.agentConfig = agentConfig.as_dict()


	return render_template('admin/agents.html', agentForm=agentForm, scripts=current_app.agentScripts, \
		addScriptForm=addScriptForm, delScriptForm=delScriptForm)

@bp.route('/agents/script/add', methods=['POST'])
@isAuthenticated
@isAdmin
def addScript():
	addScriptForm = AddScriptForm(prefix="add-script")

	if addScriptForm.validate_on_submit():
		newscript = AgentScript(name=addScriptForm.scriptName.data)
		db.session.add(newscript)
		db.session.commit()
		current_app.agentScripts = AgentScript.query.all()
		current_app.agentScriptStr = AgentScript.getScriptsString(current_app.agentScripts)
		flash("%s successfully added to scripts" % newscript.name, "success")
		return redirect(request.referrer)
	else:
		flash("%s couldn't be added to scripts" % addScriptForm.scriptName.data, "danger")
		return redirect(request.referrer)

@bp.route('/agents/script/<string:name>/delete', methods=['POST'])
@isAuthenticated
@isAdmin
def deleteScript(name):
	deleteForm = DeleteForm()

	if deleteForm.validate_on_submit():
		delScript = AgentScript.query.filter_by(name=name).first()
		if delScript:
			db.session.delete(delScript)
			db.session.commit()
			current_app.agentScripts = AgentScript.query.all()
			current_app.agentScriptStr = AgentScript.getScriptsString(current_app.agentScripts)
			flash("%s successfully deleted." % name, "success")
		else:
			flash("%s doesn't exist" % name, "danger")
		return redirect(request.referrer)

@bp.route('/scans/delete/<scan_id>', methods=['POST'])
@isAuthenticated
@isAdmin
def deleteScan(scan_id):
	delForm = DeleteForm()

	if delForm.validate_on_submit():
		deleted = current_app.elastic.delete_scan(scan_id)
		if deleted in [1,2]:
			flash("Successfully deleted scan %s." % scan_id, "success")
			if request.referrer:
				if scan_id in request.referrer:
					redirectLoc = request.referrer.rsplit(scan_id)[0]
				else:
					redirectLoc = request.referrer
			else:
				redirectLoc = url_for('main.search')
			return redirect(redirectLoc)
		else:
			flash("Could not delete scan %s." % scan_id, "danger")
			return redirect(request.referrer or url_for('main.search'))
	else:
		flash("Couldn't validate form!")
		return redirect(request.referrer)

@bp.route('/hosts/delete/<ip>', methods=['POST'])
@isAuthenticated
@isAdmin
def deleteHost(ip):
	delForm = DeleteForm()

	if delForm.validate_on_submit():
		deleted = current_app.elastic.delete_host(ip)
		if deleted > 0:
			flash("Successfully deleted host %s" % ip, "success")
			return redirect(url_for('main.search'))
		else:
			flash("Couldn't delete host: %s" % ip, "danger")
	else:
		flash("Couldn't validate form!")
		return redirect(request.referrer)

@bp.route('/tags', methods=['GET', 'POST'])
@isAuthenticated
@isAdmin
def tags():
	tags = Tag.query.all()

	addForm = AddTagForm()
	if addForm.validate_on_submit():
		newTag = Tag(name=addForm.tagname.data.lower())
		db.session.add(newTag)
		db.session.commit()
		flash('Successfully added tag %s' % newTag.name, 'success')
		return redirect(url_for('admin.tags'))
	return render_template("admin/tags.html", tags=tags, addForm=addForm)
