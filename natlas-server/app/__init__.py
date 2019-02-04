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

login = LoginManager()
login.login_view = 'auth.login'
login.login_message_category = "warning"
login.session_protection = "strong"
mail = Mail()
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
	app = Flask(__name__)
	app.config.from_object(Config)
	app.jinja_env.add_extension('jinja2.ext.do')

	db.init_app(app)
	migrate.init_app(app,db)
	login.init_app(app)
	mail.init_app(app)

	app.elastic = Elastic(app.config['ELASTICSEARCH_URL'])
	app.ScopeManager = ScopeManager()

	from app.errors import bp as errors_bp
	app.register_blueprint(errors_bp)

	from app.admin import bp as admin_bp
	app.register_blueprint(admin_bp, url_prefix='/admin')

	from app.api import bp as api_bp
	app.register_blueprint(api_bp, url_prefix='/api')

	from app.auth import bp as auth_bp
	app.register_blueprint(auth_bp, url_prefix='/auth')

	from app.main import bp as main_bp
	app.register_blueprint(main_bp)

	from app.filters import bp as filters_bp
	app.register_blueprint(filters_bp)

	return app

from app import models