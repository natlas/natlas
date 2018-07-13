import flask
from flask import render_template, request, Flask, g, url_for, flash, redirect, abort
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

from app import app, elastic, db
from app import login as lm
from app.models import User, ScopeItem
from app.forms import *
from app.email import send_password_reset_email, send_user_invite_email
from .nmap_parser import NmapParser

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
    newForm = NewScopeForm()
    delForm = ScopeDeleteForm()
    editForm = ScopeToggleForm()
    if newForm.validate_on_submit():
      newTarget = ScopeItem(target=newForm.target.data, blacklist=False)
      db.session.add(newTarget)
      db.session.commit()
      flash('Target added!', 'success')
      return redirect(url_for('admin_scope'))
    return render_template("admin/scope.html", scope=scope, delForm=delForm, editForm=editForm, newForm=newForm)
  else:
    flash("You're not an admin!", 'danger')
    return redirect(url_for('index'))

@app.route('/admin/blacklist', methods=['GET', 'POST'])
@isAuthenticated
def admin_blacklist():
  if current_user.is_admin:
    scope = ScopeItem.getBlacklist()
    newForm = NewScopeForm()
    delForm = ScopeDeleteForm()
    editForm = ScopeToggleForm()
    if newForm.validate_on_submit():
      newTarget = ScopeItem(target=newForm.target.data, blacklist=True)
      db.session.add(newTarget)
      db.session.commit()
      flash('Target blacklisted!', 'success')
      return redirect(url_for('admin_blacklist'))
    return render_template("admin/blacklist.html", scope=scope, delForm=delForm, editForm=editForm, newForm=newForm)
  else:
    flash("You're not an admin!", 'danger')
    return redirect(url_for('index'))

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
        flash('%s removed from blacklist!' % item.target, 'success')
        return redirect(url_for('admin_blacklist'))
      else:
        item.blacklist = True
        db.session.commit()
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
  count,context = elastic.search(query,app.config['RESULTS_PER_PAGE'],searchOffset)

  next_url = url_for('search', q=query, p=page + 1) \
      if count > page * app.config['RESULTS_PER_PAGE'] else None
  prev_url = url_for('search', q=query, p=page - 1) \
      if page > 1 else None

  # what kind of output are we looking for?
  if format == 'hostlist':
    return render_template("hostlist.html",query=query, numresults=count, page=page, hosts=context)
  else:
    return render_template("search.html",query=query, numresults=count, page=page, hosts=context, next_url=next_url, prev_url=prev_url)

def hostinfo(ip):
  hostinfo={}
  count,context = elastic.gethost(ip)
  if count == 0:
    return abort(404)
  hostinfo['history'] = count
  headshots=0
  headshotTypes = ['headshot', 'vncheadshot', 'httpheadshot', 'httpsheadshot']
  for hs in headshotTypes:
    if context.get(hs):
      headshots+=1
  hostinfo['headshots'] = headshots
  if context.get('hostname'):
    hostinfo['hostname'] = context.get('hostname')
  return hostinfo, context

# Create your views here.
@app.route('/host/<ip>')
@isAuthenticated
def host(ip):
  info,context = hostinfo(ip)
  return render_template("host/summary.html",**context, info=info)

@app.route('/host/<ip>/history')
@isAuthenticated
def host_history(ip):
  info,context = hostinfo(ip)
  page = int(request.args.get('p', 1))
  searchOffset = app.config['RESULTS_PER_PAGE'] * (page-1)

  count,context = elastic.gethost_history(ip, app.config['RESULTS_PER_PAGE'], searchOffset)
  if count == 0:
    abort(404)
  next_url = url_for('host_history', ip=ip, p=page + 1) \
      if count > page * app.config['RESULTS_PER_PAGE'] else None
  prev_url = url_for('host_history', ip=ip, p=page - 1) \
      if page > 1 else None

  return render_template("host/history.html", ip=ip, info=info, page=page, hosts=context,next_url=next_url, prev_url=prev_url)

@app.route('/host/<ip>/headshots')
@isAuthenticated
def host_headshots(ip):
  info,context = hostinfo(ip)
  return render_template("host/headshots.html", **context, info=info)

### API / AGENT ROUTES ###

def isAcceptableTarget(target):
  targetAddr = ipaddress.IPv4Address(target)
  inScope = False

  scope=[]
  for item in ScopeItem.getScope():
    scope.append(ipaddress.ip_network(item.target))

  for network in scope:
    if str(network).endswith('/32'):
      if targetAddr == ipaddress.IPv4Address(str(network).strip('/32')):
        inScope = True
    if targetAddr in list(network.hosts()):
      inScope = True

  if not inScope:
    return False

  blacklist=[]
  for item in ScopeItem.getBlacklist():
    blacklist.append(ipaddress.ip_network(item.target))

  for network in blacklist:
    if str(network).endswith('/32'):
      if targetAddr == ipaddress.IPv4Address(str(network).strip('/32')):
        return False
    if targetAddr in list(network.hosts()):
      return False

  return True


@app.route('/getwork')
def getwork():

  try:
    return elastic.getwork_mass()
  except:
    print("[+] Masscan data not found, selecting random target from scope.")

  random.seed(os.urandom(200))
  scope=[]
  for item in ScopeItem.getScope():
    scope.append(ipaddress.ip_network(item.target))

  blacklist=[]
  for item in ScopeItem.getBlacklist():
    blacklist.append(ipaddress.ip_network(item.target))

  # how many hosts are in scope?
  magnitude = sum(network.num_addresses for network in scope)
  blacklistSize = sum(network.num_addresses for network in blacklist)
  print("[+] Scope Size: %s IPs" % (magnitude))
  print("[+] Blacklist Size: %s IPs" % (blacklistSize))

  attempts=0
  work = {}
  work['type']='nmap'
  while attempts<1000:
    # pick one
    index = random.randint(0,magnitude-1);
    attempts = attempts+1

    target=""
    for network in scope:
      if index>=network.num_addresses:
        index-=network.num_addresses
      else:
        #target=network[index]
        isgood=True
        for badnet in blacklist: # run through the blacklist looking for match
          if network[index] in badnet:
            #print("the ip is in the blacklist! "+str(network[index]))
            isgood=False
        if isgood:
          #print("the ip is not in the blacklist! "+str(network[index]))
          work['target']=str(network[index])
          return json.dumps(work)
  return "none"

@app.route('/submit',methods=['POST'])
def submit():
  nmap = NmapParser()
  data = request.get_json()

  newhost={}
  newhost=json.loads(data)

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
