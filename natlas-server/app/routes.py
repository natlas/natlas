import flask
from flask import render_template, request, Flask, g, url_for, flash, redirect, abort, Response
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse
from netaddr import *
from functools import wraps
import time
import os
import json
import random
import sys
import traceback
import ipaddress
from datetime import datetime

from app import app, elastic, db, ScopeManager
from app import login as lm
from app.models import User, ScopeItem
from app.forms import *
from app.email import send_password_reset_email, send_user_invite_email
from .nmap_parser import NmapParser
from .util import *


@app.before_request
def before_request():
    g.preview_length = app.config['PREVIEW_LENGTH']


def isAuthenticated(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if app.config['LOGIN_REQUIRED'] and not current_user.is_authenticated:
            return lm.unauthorized()
        return f(*args, **kwargs)
    return decorated_function


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash("You're already logged in!", "info")
        return redirect(url_for('search'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('search')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('search'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('search'))
    if app.config['REGISTER_ALLOWED'].lower() == "false":
        flash("Sorry, we're not currently accepting new users. If you feel you've received this message in error, please contact an administrator.", "warning")
        return redirect(url_for('login'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('search'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password', "info")
        return redirect(url_for('login'))
    return render_template('password_reset.html',
                           title='Reset Password', form=form, pwrequest=True)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.', "success")
        return redirect(url_for('login'))
    return render_template('password_reset.html', form=form)


@app.route('/invite/<token>', methods=['GET', 'POST'])
def invite_user(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_invite_token(token)
    if not user:
        flash("Failed to verify invite token!", "danger")
        flash(User.verify_invite_token(token))
        return redirect(url_for('index'))
    form = InviteConfirmForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been set.', "success")
        return redirect(url_for('login'))
    return render_template('accept_invite.html', form=form)


@app.route('/admin', methods=['GET'])
@isAuthenticated
def admin():
    if current_user.is_admin:
        return render_template("admin/index.html")
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('index'))


@app.route('/admin/users', methods=['GET', 'POST'])
@isAuthenticated
def admin_users():
    if current_user.is_admin:
        users = User.query.all()
        delForm = UserDeleteForm()
        editForm = UserEditForm()
        inviteForm = InviteUserForm()
        if inviteForm.validate_on_submit():
            newUser = User(email=inviteForm.email.data)
            db.session.add(newUser)
            db.session.commit()
            send_user_invite_email(newUser)
            flash('Invitation Sent!', 'success')
            return redirect(url_for('admin_users'))
        return render_template("admin/users.html", users=users, delForm=delForm, editForm=editForm, inviteForm=inviteForm)
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('index'))


@app.route('/admin/users/<int:id>/delete', methods=['POST'])
@isAuthenticated
def deleteUser(id):
    if current_user.is_admin:
        delForm = UserDeleteForm()
        if delForm.validate_on_submit():
            if current_user.id == id:
                flash('You can\'t delete yourself!', 'danger')
                return redirect(url_for('admin_users'))
            user = User.query.filter_by(id=id).first()
            User.query.filter_by(id=id).delete()
            db.session.commit()
            flash('%s deleted!' % user.email, 'success')
            return redirect(url_for('admin_users'))
        else:
            flash("Form couldn't validate!", 'danger')
            return redirect(url_for('admin_users'))
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('index'))


@app.route('/admin/users/<int:id>/toggle', methods=['POST'])
@isAuthenticated
def toggleUser(id):
    if current_user.is_admin:
        editForm = UserEditForm()
        if editForm.validate_on_submit():
            user = User.query.filter_by(id=id).first()
            if user.is_admin:
                admins = User.query.filter_by(is_admin=True).all()
                if len(admins) == 1:
                    flash('Can\'t delete the last admin!', 'danger')
                    return redirect(url_for('admin_users'))
                user.is_admin = False
                db.session.commit()
                flash('User demoted!', 'success')
                return redirect(url_for('admin_users'))
            else:
                user.is_admin = True
                db.session.commit()
                flash('User promoted!', 'success')
                return redirect(url_for('admin_users'))
        else:
            flash("Form couldn't validate!", 'danger')
            return redirect(url_for('admin_users'))
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('index'))


@app.route('/admin/scope', methods=['GET', 'POST'])
@isAuthenticated
def admin_scope():
    if current_user.is_admin:
        scope = ScopeItem.getScope()
        scopeSize = ScopeManager.getScopeSize()
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
            ScopeManager.updateScope()
            flash('%s added!' % newTarget.target, 'success')
            return redirect(url_for('admin_scope'))
        return render_template("admin/scope.html", scope=scope, scopeSize=scopeSize, delForm=delForm, editForm=editForm, newForm=newForm, importForm=importForm)
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('index'))


@app.route('/admin/blacklist', methods=['GET', 'POST'])
@isAuthenticated
def admin_blacklist():
    if current_user.is_admin:
        scope = ScopeItem.getBlacklist()
        blacklistSize = ScopeManager.getBlacklistSize()
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
            ScopeManager.updateBlacklist()
            flash('%s blacklisted!' % newTarget.target, 'success')
            return redirect(url_for('admin_blacklist'))
        return render_template("admin/blacklist.html", scope=scope, blacklistSize=blacklistSize, delForm=delForm, editForm=editForm, newForm=newForm, importForm=importForm)
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('index'))


@app.route('/admin/scope/import', methods=['POST'])
@isAuthenticated
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
            ScopeManager.updateScope()
            flash('%s targets added to scope!' % successImport, 'success')
            return redirect(url_for('admin_scope'))
        else:
            for field, errors in importForm.errors.items():
                for error in errors:
                    flash(error, 'danger')
            return redirect(url_for('admin_scope'))
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('index'))


@app.route('/admin/blacklist/import', methods=['POST'])
@isAuthenticated
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
            ScopeManager.updateBlacklist()
            flash('%s targets added to blacklist!' % successImport, 'success')
            return redirect(url_for('admin_blacklist'))
        else:
            for field, errors in importForm.errors.items():
                for error in errors:
                    flash(error, 'danger')
            return redirect(url_for('admin_blacklist'))
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('index'))


@app.route('/admin/blacklist/export', methods=['GET'])
@isAuthenticated
def exportBlacklist():
    if current_user.is_admin:
        blacklistItems = ScopeItem.query.filter_by(blacklist=True).all()
        return "<br />".join(str(item.target) for item in blacklistItems)
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('index'))


@app.route('/admin/scope/export', methods=['GET'])
@isAuthenticated
def exportScope():
    if current_user.is_admin:
        scopeItems = ScopeItem.query.filter_by(blacklist=False).all()
        return "<br />".join(str(item.target) for item in scopeItems)


@app.route('/admin/scope/<int:id>/delete', methods=['POST'])
@isAuthenticated
def deleteScopeItem(id):
    if current_user.is_admin:
        delForm = ScopeDeleteForm()
        if delForm.validate_on_submit():
            item = ScopeItem.query.filter_by(id=id).first()
            if item.blacklist:
                redirectLoc = 'admin_blacklist'
            else:
                redirectLoc = 'admin_scope'
            ScopeItem.query.filter_by(id=id).delete()
            db.session.commit()
            ScopeManager.update()
            flash('%s deleted!' % item.target, 'success')
            return redirect(url_for(redirectLoc))
        else:
            flash("Form couldn't validate!", 'danger')
            return redirect(url_for(redirectLoc))
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('index'))


@app.route('/admin/scope/<int:id>/toggle', methods=['POST'])
@isAuthenticated
def toggleScopeItem(id):
    if current_user.is_admin:
        toggleForm = ScopeToggleForm()
        if toggleForm.validate_on_submit():
            item = ScopeItem.query.filter_by(id=id).first()
            if item.blacklist:
                item.blacklist = False
                db.session.commit()
                ScopeManager.update()
                flash('%s removed from blacklist!' % item.target, 'success')
                return redirect(url_for('admin_blacklist'))
            else:
                item.blacklist = True
                db.session.commit()
                ScopeManager.update()
                flash('%s blacklisted!' % item.target, 'success')
                return redirect(url_for('admin_scope'))
        else:
            flash("Form couldn't validate!", 'danger')
            return redirect(url_for('admin_scope'))
    else:
        flash("You're not an admin!", 'danger')
        return redirect(url_for('index'))


@app.route('/')
@isAuthenticated
def index():
    return redirect(url_for('search'))


@app.route('/search')
@isAuthenticated
def search():
    query = request.args.get('q', '')
    page = int(request.args.get('p', 1))
    format = request.args.get('f', "")

    searchOffset = app.config['RESULTS_PER_PAGE'] * (page-1)
    count, context = elastic.search(
        query, app.config['RESULTS_PER_PAGE'], searchOffset)

    next_url = url_for('search', q=query, p=page + 1) \
        if count > page * app.config['RESULTS_PER_PAGE'] else None
    prev_url = url_for('search', q=query, p=page - 1) \
        if page > 1 else None

    # what kind of output are we looking for?
    if format == 'hostlist':
        hostlist = []
        for host in context:
            hostlist.append(str(host['ip']))
        return Response('\n'.join(hostlist), mimetype='text/plain')
    else:
        return render_template("search.html", query=query, numresults=count, page=page, hosts=context, next_url=next_url, prev_url=prev_url)


# Create your views here.
@app.route('/host/<ip>')
@app.route('/host/<ip>/')
@isAuthenticated
def host(ip):
    info, context = hostinfo(ip)
    return render_template("host/summary.html", **context, info=info)


@app.route('/host/<ip>/history')
@app.route('/host/<ip>/history/')
@isAuthenticated
def host_history(ip):
    info, context = hostinfo(ip)
    page = int(request.args.get('p', 1))
    searchOffset = app.config['RESULTS_PER_PAGE'] * (page-1)

    count, context = elastic.gethost_history(
        ip, app.config['RESULTS_PER_PAGE'], searchOffset)
    if count == 0:
        abort(404)
    next_url = url_for('host_history', ip=ip, p=page + 1) \
        if count > page * app.config['RESULTS_PER_PAGE'] else None
    prev_url = url_for('host_history', ip=ip, p=page - 1) \
        if page > 1 else None

    return render_template("host/history.html", ip=ip, info=info, page=page, hosts=context, next_url=next_url, prev_url=prev_url)

@app.route('/host/<ip>/<scan_id>')
@isAuthenticated
def host_historical_result(ip, scan_id):

    info, context = hostinfo(ip)
    count, context = elastic.gethost_scan_id(
        ip, scan_id)
    return render_template("host/summary.html", info=info, **context)

@app.route('/host/<ip>/<scan_id>.xml')
@isAuthenticated
def export_scan_xml(ip, scan_id):
    
    count, context = elastic.gethost_scan_id(
        ip, scan_id)
    return Response(context['xml_data'], mimetype="text/plain")

@app.route('/host/<ip>/<scan_id>.nmap')
@isAuthenticated
def export_scan_nmap(ip, scan_id):
    
    count, context = elastic.gethost_scan_id(
        ip, scan_id)
    return Response(context['nmap_data'], mimetype="text/plain")

@app.route('/host/<ip>/<scan_id>.gnmap')
@isAuthenticated
def export_scan_gnmap(ip, scan_id):
    
    count, context = elastic.gethost_scan_id(
        ip, scan_id)
    return Response(context['gnmap_data'], mimetype="text/plain")

@app.route('/host/<ip>/headshots')
@app.route('/host/<ip>/headshots/')
@isAuthenticated
def host_headshots(ip):

    info, context = hostinfo(ip)
    return render_template("host/headshots.html", **context, info=info)

### API / AGENT ROUTES ###


@app.route('/getwork')
def getwork():

    random.seed(os.urandom(200))

    # how many hosts are in scope?
    scopeSize = ScopeManager.getScopeSize()
    blacklistSize = ScopeManager.getBlacklistSize()
    if scopeSize == 0:
        return "Scope Not Found", 404, {'content-type':'text/plain'}

    attempts = 0
    work = {}
    work['type'] = 'nmap'
    while attempts < 1000:
        # pick one
        index = random.randint(0, scopeSize-1)
        attempts = attempts+1

        target = ""
        for network in ScopeManager.getScope():
            if index >= network.num_addresses:
                index -= network.num_addresses
            else:
                isgood = True
                for badnet in ScopeManager.getBlacklist():  # run through the blacklist looking for match
                    if network[index] in badnet:
                        isgood = False
                if isgood:
                    work['target'] = str(network[index])
                    return json.dumps(work), 200, {'content-type':'application/json'}
    return "Couldn't find a target that wasn't blacklisted.", 404, {'content-type':'text/plain'}


@app.route('/submit', methods=['POST'])
def submit():
    nmap = NmapParser()
    data = request.get_json()

    newhost = {}
    newhost = json.loads(data)

    if not nmap.has_scan_report(newhost['nmap_data']):
        return "[!] No scan report found! Make sure your scan includes \"%s\"" % nmap.REPORT

    try:
        newhost['ip'] = nmap.get_ip(newhost['nmap_data'])
        if not isAcceptableTarget(newhost['ip']):
            return "[!] This address isn't in our authorized scope!"
        newhost['hostname'] = nmap.get_hostname(newhost['nmap_data'])
        newhost['ports'] = str(nmap.get_ports(newhost['nmap_data']))
        newhost['ctime'] = datetime.now()
    except Exception as e:
        return "[!] Couldn't find necessary nmap_data\n" + str(e)

    if len(newhost['ports']) == 0:
        return "[!] No open ports found!"

    if len(newhost['ports']) > 500:
        return "[!] More than 500 ports found. This is probably an IDS/IPS. We're going to throw the data out."

    elastic.newhost(newhost)

    return "[+] nmap successful and submitted for ip: "+newhost['ip']
