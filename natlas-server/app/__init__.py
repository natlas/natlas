import os

from flask import Flask, flash, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, AnonymousUserMixin, current_user
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from webpack_manifest import webpack_manifest

import config
from app.elastic import ElasticInterface
from .instrumentation import initialize_opencensus


class AnonUser(AnonymousUserMixin):

    results_per_page = 50
    preview_length = 50


login = LoginManager()
login.login_view = "auth.login"
login.anonymous_user = AnonUser
login.login_message_category = "warning"
login.session_protection = "strong"
mail = Mail()
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


@login.unauthorized_handler
def unauthorized():
    if current_user.is_anonymous:
        flash("You must login to continue.", "warning")
        return redirect(url_for("auth.login"))
    if not current_user.is_admin:
        flash(f"You must be an admin to access {request.path}.", "warning")
        return redirect(url_for("main.index"))


def load_natlas_config(app):
    if not db.engine.has_table("config_item"):
        return

    updated_items = 0
    from app.models import ConfigItem

    # Look to see if any new config items were added that aren't currently in db
    default_configs = config.get_defaults()
    for key, item in default_configs:
        conf_item = ConfigItem.query.filter_by(name=key).first()
        if not conf_item:
            conf_item = ConfigItem(name=key, type=item["type"], value=item["default"])
            db.session.add(conf_item)
            updated_items += 1
        app.config[conf_item.name] = config.casted_value(
            conf_item.type, conf_item.value
        )
    if updated_items > 0:
        db.session.commit()


def load_natlas_services(app):
    if not db.engine.has_table("natlas_services"):
        return
    from app.models import NatlasServices

    current_services = NatlasServices.query.order_by(NatlasServices.id.desc()).first()
    if not current_services:
        # Let's populate server defaults
        defaultServices = (
            open(os.path.join(app.config["BASEDIR"], "defaults/natlas-services"))
            .read()
            .rstrip("\r\n")
        )
        current_services = NatlasServices(services=defaultServices)
        db.session.add(current_services)
        db.session.commit()
        print("NatlasServices populated with defaults")
    app.current_services = current_services.as_dict()


def load_agent_config(app):
    if not db.engine.has_table("agent_config"):
        return
    # Load the current agent config, otherwise create it.
    from app.models import AgentConfig

    agentConfig = AgentConfig.query.get(
        1
    )  # the agent config is updated in place so only 1 record
    if not agentConfig:
        agentConfig = AgentConfig()  # populate an agent config with database defaults
        db.session.add(agentConfig)
        db.session.commit()
        print("AgentConfig populated with defaults")
    app.agentConfig = agentConfig.as_dict()


def load_agent_scripts(app):
    if not db.engine.has_table("agent_script"):
        return
    # Load the current agent config, otherwise create it.
    from app.models import AgentScript

    agentScripts = AgentScript.query.all()
    if not agentScripts:
        defaultAgentScript = AgentScript(name="default")
        db.session.add(defaultAgentScript)
        db.session.commit()
        print("AgentScript populated with default")
        agentScripts = [defaultAgentScript]
    app.agentScripts = agentScripts
    app.agentScriptStr = AgentScript.getScriptsString(scriptList=agentScripts)


def create_app(config_class=config.Config, load_config=False):
    app = Flask(__name__)
    initialize_opencensus(config_class, app)

    app.config.from_object(config_class)
    app.jinja_env.add_extension("jinja2.ext.do")
    app.elastic = ElasticInterface(app.config["ELASTICSEARCH_URL"])
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    app.config["webpack"] = webpack_manifest.load(
        # An absolute path to a manifest file
        path=os.path.join(
            app.config["BASEDIR"], "app", "static", "dist", "webpack_manifest.json"
        ),
        # The root url that your static assets are served from
        static_url="/static/",
    )

    with app.app_context():
        load_natlas_config(app)
        load_natlas_services(app)
        load_agent_config(app)
        load_agent_scripts(app)

    from app.scope import ScopeManager

    app.ScopeManager = ScopeManager()

    from app.errors import bp as errors_bp

    app.register_blueprint(errors_bp)

    from app.admin import bp as admin_bp

    app.register_blueprint(admin_bp, url_prefix="/admin")

    from app.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    csrf.exempt(api_bp)

    from app.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.user import bp as user_bp

    app.register_blueprint(user_bp, url_prefix="/user")

    from app.host import bp as host_bp

    app.register_blueprint(host_bp, url_prefix="/host")

    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    from app.filters import bp as filters_bp

    app.register_blueprint(filters_bp)

    return app


from app import models  # noqa: F401
