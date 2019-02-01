from flask import render_template, redirect, url_for, current_app, flash
from flask_login import current_user
from app import db
from app.admin import bp
from app.admin.forms import UserDeleteForm, UserEditForm, InviteUserForm, \
    NewScopeForm, ImportScopeForm, ScopeToggleForm, ScopeDeleteForm
from app.models import User, ScopeItem
from app.auth.email import send_user_invite_email
from app.auth.wrappers import isAuthenticated, isAdmin

@bp.route('/', methods=['GET'])
@isAuthenticated
@isAdmin
def admin():
    if current_user.is_admin:
        return render_template("admin/index.html")
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('main.index'))


@bp.route('/users', methods=['GET', 'POST'])
@isAuthenticated
@isAdmin
def users():
    if current_user.is_admin:
        users = User.query.all()
        delForm = UserDeleteForm()
        editForm = UserEditForm()
        inviteForm = InviteUserForm()
        if inviteForm.validate_on_submit():
            newUser = User(email=inviteForm.email.data)
            db.session.add(newUser)
            send_user_invite_email(newUser)
            db.session.commit()
            flash('Invitation Sent!', 'success')
            return redirect(url_for('admin.users'))
        return render_template("admin/users.html", users=users, delForm=delForm, editForm=editForm, inviteForm=inviteForm)
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('main.index'))


@bp.route('/users/<int:id>/delete', methods=['POST'])
@isAuthenticated
@isAdmin
def deleteUser(id):
    if current_user.is_admin:
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
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('main.index'))


@bp.route('/users/<int:id>/toggle', methods=['POST'])
@isAuthenticated
@isAdmin
def toggleUser(id):
    if current_user.is_admin:
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
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('main.index'))


@bp.route('/scope', methods=['GET', 'POST'])
@isAuthenticated
@isAdmin
def scope():
    if current_user.is_admin:
        scope = ScopeItem.getScope()
        scopeSize = current_app.ScopeManager.getScopeSize()
        if scopeSize == 0: # if it's zero, let's update the app's scopemanager
            current_app.ScopeManager.update()
            scopeSize = current_app.ScopeManager.getScopeSize() # if it's zero again that's fine, we just had to check
        newForm = NewScopeForm()
        delForm = ScopeDeleteForm()
        editForm = ScopeToggleForm()
        importForm = ImportScopeForm()
        if newForm.validate_on_submit():
            if '/' not in newForm.target.data:
                newForm.target.data = newForm.target.data + '/32'
            newTarget = ScopeItem(target=newForm.target.data, blacklist=False)
            db.session.add(newTarget)
            db.session.commit()
            current_app.ScopeManager.updateScope()
            flash('%s added!' % newTarget.target, 'success')
            return redirect(url_for('admin.scope'))
        return render_template("admin/scope.html", scope=scope, scopeSize=scopeSize, delForm=delForm, editForm=editForm, newForm=newForm, importForm=importForm)
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('main.index'))


@bp.route('/blacklist', methods=['GET', 'POST'])
@isAuthenticated
@isAdmin
def blacklist():
    if current_user.is_admin:
        scope = ScopeItem.getBlacklist()
        blacklistSize = current_app.ScopeManager.getBlacklistSize()
        newForm = NewScopeForm()
        delForm = ScopeDeleteForm()
        editForm = ScopeToggleForm()
        importForm = ImportScopeForm()
        if newForm.validate_on_submit():
            if '/' not in newForm.target.data:
                newForm.target.data = newForm.target.data + '/32'
            newTarget = ScopeItem(target=newForm.target.data, blacklist=True)
            db.session.add(newTarget)
            db.session.commit()
            current_app.ScopeManager.updateBlacklist()
            flash('%s blacklisted!' % newTarget.target, 'success')
            return redirect(url_for('admin.blacklist'))
        return render_template("admin/blacklist.html", scope=scope, blacklistSize=blacklistSize, delForm=delForm, editForm=editForm, newForm=newForm, importForm=importForm)
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('main.index'))


@bp.route('/scope/import', methods=['POST'])
@isAuthenticated
@isAdmin
def importScope():
    if current_user.is_admin:
        importForm = ImportScopeForm()
        if importForm.validate_on_submit():
            successImport = 0
            newScopeItems = importForm.scope.data.split('\n')
            for item in newScopeItems:
                item = item.strip()
                if '/' not in item:
                    item = item + '/32'
                exists = ScopeItem.query.filter_by(target=item).first()
                if exists:
                    continue
                newTarget = ScopeItem(target=item, blacklist=False)
                db.session.add(newTarget)
                db.session.commit()
                successImport += 1
            current_app.ScopeManager.updateScope()
            flash('%s targets added to scope!' % successImport, 'success')
            return redirect(url_for('admin.scope'))
        else:
            for field, errors in importForm.errors.items():
                for error in errors:
                    flash(error, 'danger')
            return redirect(url_for('admin.scope'))
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('main.index'))


@bp.route('/blacklist/import', methods=['POST'])
@isAuthenticated
@isAdmin
def importBlacklist():
    if current_user.is_admin:
        importForm = ImportScopeForm()
        if importForm.validate_on_submit():
            successImport = 0
            newScopeItems = importForm.scope.data.split('\n')
            for item in newScopeItems:
                item = item.strip()
                if '/' not in item:
                    item = item + '/32'
                exists = ScopeItem.query.filter_by(target=item).first()
                if exists:
                    continue
                newTarget = ScopeItem(target=item, blacklist=True)
                db.session.add(newTarget)
                db.session.commit()
                successImport += 1
            current_app.ScopeManager.updateBlacklist()
            flash('%s targets added to blacklist!' % successImport, 'success')
            return redirect(url_for('admin.blacklist'))
        else:
            for field, errors in importForm.errors.items():
                for error in errors:
                    flash(error, 'danger')
            return redirect(url_for('admin.blacklist'))
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('main.index'))


@bp.route('/blacklist/export', methods=['GET'])
@isAuthenticated
@isAdmin
def exportBlacklist():
    if current_user.is_admin:
        blacklistItems = ScopeItem.query.filter_by(blacklist=True).all()
        return "<br />".join(str(item.target) for item in blacklistItems)
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('main.index'))


@bp.route('/scope/export', methods=['GET'])
@isAuthenticated
@isAdmin
def exportScope():
    if current_user.is_admin:
        scopeItems = ScopeItem.query.filter_by(blacklist=False).all()
        return "<br />".join(str(item.target) for item in scopeItems)


@bp.route('/scope/<int:id>/delete', methods=['POST'])
@isAuthenticated
@isAdmin
def deleteScopeItem(id):
    if current_user.is_admin:
        delForm = ScopeDeleteForm()
        if delForm.validate_on_submit():
            item = ScopeItem.query.filter_by(id=id).first()
            if item.blacklist:
                redirectLoc = 'admin.blacklist'
            else:
                redirectLoc = 'admin.scope'
            ScopeItem.query.filter_by(id=id).delete()
            db.session.commit()
            current_app.ScopeManager.update()
            flash('%s deleted!' % item.target, 'success')
            return redirect(url_for(redirectLoc))
        else:
            flash("Form couldn't validate!", 'danger')
            return redirect(url_for(redirectLoc))
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('main.index'))


@bp.route('/scope/<int:id>/toggle', methods=['POST'])
@isAuthenticated
@isAdmin
def toggleScopeItem(id):
    if current_user.is_admin:
        toggleForm = ScopeToggleForm()
        if toggleForm.validate_on_submit():
            item = ScopeItem.query.filter_by(id=id).first()
            if item.blacklist:
                item.blacklist = False
                db.session.commit()
                current_app.ScopeManager.update()
                flash('%s removed from blacklist!' % item.target, 'success')
                return redirect(url_for('admin.blacklist'))
            else:
                item.blacklist = True
                db.session.commit()
                current_app.ScopeManager.update()
                flash('%s blacklisted!' % item.target, 'success')
                return redirect(url_for('admin.scope'))
        else:
            flash("Form couldn't validate!", 'danger')
            return redirect(url_for('admin.scope'))
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('main.index'))