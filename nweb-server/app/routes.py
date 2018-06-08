import flask
from flask import render_template, request, Flask, g, url_for, flash, redirect, current_app
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
from datetime import datetime

from app import app, elastic, db
from app import login as lm
from app.models import User
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm, InviteUserForm
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
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
    flash('Your password has been reset.', "info")
    return redirect(url_for('login'))
  return render_template('password_reset.html', form=form)

# Create your views here.
@app.route('/host')
@isAuthenticated
def host():
  host = request.args.get('h')
  context = elastic.gethost(host)
  return render_template("host.html",**context)

@app.route('/admin', methods=['GET', 'POST'])
@isAuthenticated
def admin():
  inviteForm = InviteUserForm()
  if inviteForm.validate_on_submit():
    newUser = User(email=inviteForm.email.data)
    db.session.add(newUser)
    db.session.commit()
    send_user_invite_email(newUser)
    flash('Invitation Sent!', 'success')
    return redirect(url_for('admin'))
  return render_template("admin.html", inviteForm=inviteForm)

@app.route('/')
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

@app.route('/getwork')
def getwork():

  try:
    return elastic.getwork_mass()
  except:
    print("[+] Masscan data not found, selecting random target from scope.")

  random.seed(os.urandom(200))
  scope=[]
  try:
    for line in open(app.config['SCOPE_DOC']):
      try:
        scope.append(IPNetwork(line))
      except:
        print("[!] Line %s in %s failed to parse" % (line, app.config['SCOPE_DOC']))
  except:
    print("[!] Failed to find %s" % app.config['SCOPE_DOC'])
    scope=[]
    scope.append(IPNetwork("127.0.0.1"))

  blacklist=[]
  try:
    for line in open(app.config['BLACKLIST_DOC']):
      blacklist.append(IPNetwork(line))
  except Exception as e:
    print("[!] Failed to parse %s :"+str(e)[:-1]+" '"+line[:-1]+"'" % app.config['BLACKLIST_DOC'])
    blacklist=[]

  # how many hosts are in scope?
  magnitude = sum(len(network) for network in scope)
  print("[+] There are %s IPs in %s" % (magnitude, app.config['SCOPE_DOC']))

  attempts=0
  work = {}
  work['type']='nmap'
  while attempts<1000:
    # pick one
    index = random.randint(0,magnitude-1);
    attempts = attempts+1

    target=""
    for network in scope:
      if index>=len(network):
        index-=len(network)
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
