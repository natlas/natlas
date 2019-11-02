from flask import Flask, flash, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, AnonymousUserMixin, current_user
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from config import Config, populate_defaults, get_defaults
from app.elastic import Elastic
from app.scope import ScopeManager
from urllib.parse import urlparse
import sqlalchemy
import os
import hashlib
import sentry_sdk

class AnonUser(AnonymousUserMixin):

	results_per_page = 50
	preview_length = 50


login = LoginManager()
login.login_view = 'auth.login'
login.anonymous_user = AnonUser
login.login_message_category = "warning"
login.session_protection = "strong"
mail = Mail()
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


def initialize_sentryio(config):
	if config.sentry_dsn:
		url = urlparse(config.sentry_dsn)
		print("Sentry.io enabled and reporting errors to %s://%s." % (url.scheme, url.hostname))
		from sentry_sdk.integrations.flask import FlaskIntegration
		sentry_sdk.init(dsn=config.sentry_dsn, release=config.NATLAS_VERSION, integrations=[FlaskIntegration()])


@login.unauthorized_handler
def unauthorized():
	if current_user.is_anonymous:
		flash("You must login to continue.", "warning")
		return redirect(url_for('auth.login'))
	if not current_user.is_admin:
		flash("You must be an admin to access %s." % request.path, "warning")
		return redirect(url_for('main.index'))


def create_app(config_class=Config, load_config=False):
	initialize_sentryio(config_class)
	app = Flask(__name__)
	app.config.from_object(Config)
	app.jinja_env.add_extension('jinja2.ext.do')

	db.init_app(app)
	migrate.init_app(app,db)
	login.init_app(app)
	mail.init_app(app)
	csrf.init_app(app)

	if load_config:
		print("Loading Config from database")
		with app.app_context():
			from app.models import ConfigItem
			try: # This is gross but we need it because otherwise flask db operations won't work to create the ConfigItem table in the first place.

				# Look to see if any new config items were added that aren't currently in db
				for item in get_defaults():
					if not ConfigItem.query.filter_by(name=item[0]).first():
						newConfItem = ConfigItem(name=item[0], type=item[1], value=item[2])
						db.session.add(newConfItem)
						db.session.commit()

				conf = ConfigItem.query.all()
				if not conf: # We'll hit this if the table exists but there's no data
					populate_defaults(verbose=False)
					conf = ConfigItem.query.all() # populate_defaults should populate data that we can query now
					if not conf: # if it didn't, then we don't have config items that we need in order to run, so exit.
						raise(SystemExit())

				for item in conf:
					if item.type == "int":
						app.config[item.name] = int(item.value)
					elif item.type == "bool":
						if item.value == "True":
							app.config[item.name] = True
						else:
							app.config[item.name] = False
					elif item.type == "string":
						app.config[item.name] = item.value
					else:
						print("Unsupported config type %s:%s:%s" % (item.name, item.type, item.value))
			except Exception as e:
				print("ConfigItem table doesn't exist yet. Ignore if flask db upgrade.")

			from app.models import NatlasServices
			try:
				current_services = NatlasServices.query.order_by(NatlasServices.id.desc()).first()
				if current_services:
					app.current_services = current_services.as_dict()
				else: # Let's populate server defaults
					defaultServices = open(os.path.join(app.config["BASEDIR"], "defaults/natlas-services")).read().rstrip('\r\n')
					defaultSha = hashlib.sha256(defaultServices.encode()).hexdigest()
					current_services = NatlasServices(sha256=defaultSha, services=defaultServices) # default values until we load something
					db.session.add(current_services)
					db.session.commit()
					print("NatlasServices populated with defaults from defaults/natlas-services")
					app.current_services = current_services.as_dict()
			except Exception as e:
				print("NatlasServices table doesn't exist yet. Ignore if flask db upgrade.")

			# Load the current agent config, otherwise create it.
			from app.models import AgentConfig
			try:
				agentConfig = AgentConfig.query.get(1) # the agent config is updated in place so only 1 record
				if agentConfig:
					app.agentConfig = agentConfig.as_dict()
				else:
					newAgentConfig = AgentConfig() # populate an agent config with database defaults
					db.session.add(newAgentConfig)
					db.session.commit()
					print("AgentConfig populated with defaults")
					app.agentConfig = newAgentConfig.as_dict()
			except Exception as e:
				print("AgentConfig table doesn't exist yet. Ignore if flask db upgrade.")

			# Load the current agent config, otherwise create it.
			from app.models import AgentScript
			try:
				agentScripts = AgentScript.query.all()
				if not agentScripts:
					defaultAgentScript = AgentScript(name="default")
					db.session.add(defaultAgentScript)
					db.session.commit()
					print("AgentScript populated with default")
					agentScripts = AgentScript.query.all()
				app.agentScripts = agentScripts
				app.agentScriptStr = AgentScript.getScriptsString(scriptList=agentScripts)
			except Exception as e:
				print("AgentScript table doesn't exist yet. Ignore if flask db upgrade.")

		# Grungy thing so we can use flask db and flask shell before the config items are initially populated
		if "ELASTICSEARCH_URL" in app.config:
			app.elastic = Elastic(app.config['ELASTICSEARCH_URL'])

	app.ScopeManager = ScopeManager()

	from app.errors import bp as errors_bp
	app.register_blueprint(errors_bp)

	from app.admin import bp as admin_bp
	app.register_blueprint(admin_bp, url_prefix='/admin')

	from app.api import bp as api_bp
	app.register_blueprint(api_bp, url_prefix='/api')
	csrf.exempt(api_bp)

	from app.auth import bp as auth_bp
	app.register_blueprint(auth_bp, url_prefix='/auth')

	from app.user import bp as user_bp
	app.register_blueprint(user_bp, url_prefix='/user')

	from app.main import bp as main_bp
	app.register_blueprint(main_bp)

	from app.filters import bp as filters_bp
	app.register_blueprint(filters_bp)

	return app

from app import models
