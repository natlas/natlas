from time import time
from app import db
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login
from datetime import datetime, timezone
from email_validator import validate_email, EmailNotValidError
import jwt, string, random
from .util import utcnow_tz

# Many:Many table mapping scope items to tags and vice versa.
scopetags = db.Table('scopetags',
    db.Column('scope_id', db.Integer, db.ForeignKey('scope_item.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

# Users and related configs
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    results_per_page = db.Column(db.Integer, default=100)
    preview_length = db.Column(db.Integer, default=100)
    rescans = db.relationship('RescanTask', backref='submitter', lazy='select')
    agents = db.relationship('Agent', backref='user', lazy=True)

    def __repr__(self):
        return '<User {}>'.format(self.email)

    # https://github.com/JoshData/python-email-validator
    @staticmethod
    def validate_email(email):
        try:
            valid = validate_email(email)
            email = valid["email"]
            return email
        except EmailNotValidError as e:
            return False

    # This is really only used by the add-user bootstrap script, but useful to contain it here.
    @staticmethod
    def generate_password(length):
        passcharset = string.ascii_uppercase + string.ascii_lowercase + string.digits
        return ''.join(random.SystemRandom().choice(passcharset) for _ in range(length))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def get_invite_token(self, expires_in=172800):
        return jwt.encode(
            {'invite_user': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_invite_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['invite_user']
        except:
            return
        return User.query.get(id)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Scope and blacklist items
class ScopeItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target = db.Column(db.String, index=True, unique=True)
    blacklist = db.Column(db.Boolean, index=True)
    tags = db.relationship('Tag', secondary=scopetags,
        primaryjoin=(scopetags.c.scope_id == id),
        backref=db.backref('scope', lazy='dynamic'), lazy='dynamic')

    def getBlacklist():
        return ScopeItem.query.filter_by(blacklist=True).all()

    def getScope():
        return ScopeItem.query.filter_by(blacklist=False).all()

    def addTag(self, tag):
        if not self.is_tagged(tag):
            self.tags.append(tag)

    def delTag(self, tag):
        if self.is_tagged(tag):
            self.tags.remove(tag)

    def is_tagged(self, tag):
        return self.tags.filter(scopetags.c.tag_id == tag.id).count() > 0

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Server configuration options
# This uses a generic key,value style schema so that we can avoid changing the model for every new feature
# Default config options are defined in natlas-server/config.py
class ConfigItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)
    type = db.Column(db.String(256))
    value = db.Column(db.String(256))
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# While generally I prefer to use a singular model name, each record here is going to be storing a set of services
# Each record in this table is a complete nmap-services db
class NatlasServices(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sha256 = db.Column(db.String(64))
    services = db.Column(db.Text)

    def services_as_list(self):
        servlist = []
        idx = 1
        for line in self.services.splitlines():
            # any empty newlines will be skipped, or comment lines (for uploaded files)
            if line == '' or line.startswith('#'):
                continue

            # split on whitespace, store as tuple
            portnum = line.split()[1].split('/')[0]
            portproto = line.split()[1].split('/')[1]
            servlist.append((idx, portnum, portproto, line.split()[0]))
            idx += 1
        return servlist

    def as_dict(self):
        servdict = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        servdict['as_list'] = self.services_as_list()
        return servdict


# Agent configuration options
class AgentConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    versionDetection = db.Column(db.Boolean, default=True) # Enable Version Detection (-sV)
    osDetection = db.Column(db.Boolean, default=True) # Enable OS Detection (-O)
    enableScripts = db.Column(db.Boolean, default=True) # Enable Nmap Scripting Engine (loads all AgentScripts)
    onlyOpens = db.Column(db.Boolean, default=True) # Only report open ports (--open)
    scanTimeout = db.Column(db.Integer, default=660) # SIGKILL nmap if it's running longer than this
    webScreenshots = db.Column(db.Boolean, default=True) # Attempt to take web screenshots (aquatone)
    vncScreenshots = db.Column(db.Boolean, default=True) # Attempt to take VNC screenshots (xvfb+vncsnapshot)

    scriptTimeout = db.Column(db.Integer, default=60) # --script-timeout (s)
    hostTimeout = db.Column(db.Integer, default=600) # --host-timeout (s)
    osScanLimit = db.Column(db.Boolean, default=True) # --osscan-limit
    noPing = db.Column(db.Boolean, default=False) # -Pn
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Scripts for agents to run
# These will be named according to the command line value that gets passed to nmap
# groups of scripts are also accepted, such as "safe" and "default"
# auth, broadcast, default. discovery, dos, exploit, external, fuzzer, intrusive, malware, safe, version, and vuln
# https://nmap.org/book/nse-usage.html#nse-categories
class AgentScript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, index=True, unique=True)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @staticmethod
    def getScriptsString(scriptList=None):
        if scriptList: # optionally pass in existing query and convert to string
            return ','.join(s.name for s in scriptList)
        return ','.join(s.name for s in AgentScript.query.all())


# Rescan Queue
# Each record represents a user-requested rescan of a given target.
# Tracks when it was dispatched, when it was completed, and the scan id of the complete scan.
class RescanTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_added = db.Column(db.DateTime, index=True, default=utcnow_tz, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target = db.Column(db.String, index=True, nullable=False)
    dispatched = db.Column(db.Boolean, default=False, index=True)
    date_dispatched = db.Column(db.DateTime, index=True)
    complete = db.Column(db.Boolean, default=False, index=True)
    date_completed = db.Column(db.DateTime, index=True)
    scan_id = db.Column(db.String, index=True, unique=True)

    def dispatchTask(self):
        self.dispatched = True
        self.date_dispatched = utcnow_tz()

    def completeTask(self, scan_id):
        self.scan_id = scan_id
        self.complete = True
        self.date_completed = utcnow_tz()

    @staticmethod
    def getPendingTasks(): # Tasks that haven't been completed and haven't been dispatched
        return RescanTask.query.filter_by(complete=False).filter_by(dispatched=False).all()

    @staticmethod
    def getDispatchedTasks(): # Tasks that have been dispatched but haven't been completed
        return RescanTask.query.filter_by(dispatched=True).filter_by(complete=False).all()

    @staticmethod
    def getIncompleteTasks(): #All tasks that haven't been marked as complete
        return RescanTask.query.filter_by(complete=False).all()

    @staticmethod
    def getIncompleteTaskForTarget(ip):
        return RescanTask.query.filter_by(target=ip).filter_by(complete=False).all()

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Simple tags that can be added to scope items for automatic tagging
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, index=True, unique=True, nullable=False)


# Agent registration
# Users can have many agents, each agent has an ID and a secret (token)
# Friendly name is purely for identification of agents in the management page
class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # agent identification string for storing in reports
    agentid = db.Column(db.String(16), index=True, unique=True, nullable=False) 
    date_created = db.Column(db.DateTime, nullable=False, default=utcnow_tz)
    # auth token
    token = db.Column(db.String(32), index=True, unique=True)
    # optional friendly name for viewing on user page
    friendly_name = db.Column(db.String(32), default="")

    def verify_token(self, token):
        if self.token == token:
            return True
        return False

    @staticmethod
    def load_agent(agentid):
        return Agent.query.filter_by(agentid=agentid).first()

    @staticmethod
    def generate_token():
        return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(32))

    @staticmethod
    def generate_agentid():
        return "%x" % random.randrange(16**16)
