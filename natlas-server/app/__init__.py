from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from app.elastic import Elastic
from app.scope import ScopeManager
import sqlalchemy
import os

app = Flask(__name__)
app.config.from_object(Config)
app.jinja_env.add_extension('jinja2.ext.do')

login = LoginManager(app)
login.login_view = 'login'
login.login_message_category = "warning"
login.session_protection = "strong"

mail = Mail(app)

elastic = Elastic(app.config['ELASTICSEARCH_URL'])
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import routes, models

# super gross hack that enables flask db operations when the databse doesn't already exist
try:
    ScopeManager = ScopeManager()
    ScopeManager.update()
except sqlalchemy.exc.OperationalError as e:
    print("[!] Scope Manager could not find metadata.db: %s" %
          app.config['SQLALCHEMY_DATABASE_URI'])
