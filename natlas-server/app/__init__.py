import os

import config
from flask import Flask, flash, redirect, request, url_for
from flask_login import AnonymousUserMixin, LoginManager, current_user
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from migrations.migrator import handle_db_upgrade, migration_needed
from sqlalchemy.orm import DeclarativeBase
from webpack_manifest import webpack_manifest

from app.config_loader import load_config_from_db
from app.elastic import ElasticInterface
from app.instrumentation import initialize_opentelemetry
from app.scope import ScopeManager
from app.url_converters import register_converters


class AnonUser(AnonymousUserMixin):  # type: ignore[misc]
    results_per_page = 50
    preview_length = 50


class NatlasBase(DeclarativeBase):
    pass


login = LoginManager()
login.login_view = "auth.login"
login.anonymous_user = AnonUser
login.login_message_category = "warning"
login.session_protection = "strong"
mail = Mail()
db = SQLAlchemy(model_class=NatlasBase)
migrate = Migrate()
csrf = CSRFProtect()
scope_manager = ScopeManager()


@login.unauthorized_handler
def unauthorized():  # type: ignore[no-untyped-def]
    if current_user.is_anonymous:
        flash("You must login to continue.", "warning")
        return redirect(url_for("auth.login"))
    if not current_user.is_admin:
        flash(f"You must be an admin to access {request.path}.", "warning")
        return redirect(url_for("main.index"))
    flash("Unauthorized", "warning")
    return redirect(url_for("auth.login"))


def create_app(config_class=config.Config, migrating=False):  # type: ignore[no-untyped-def]
    app = Flask(__name__)
    config = config_class

    app.config.from_object(config)
    initialize_opentelemetry(config, app)
    db.init_app(app)
    migrate.init_app(app, db)

    # If we're being called with migrating=True then return early to allow the migration
    if migrating:
        return app

    # If a migration is needed, try to automatically handle it, otherwise bail out
    if migration_needed(
        app.config["SQLALCHEMY_DATABASE_URI"]
    ) and not handle_db_upgrade(app):
        raise RuntimeError(
            "[!] Database migration required and DB_AUTO_UPGRADE is not enabled"
        )

    app.jinja_env.add_extension("jinja2.ext.do")
    app.elastic = ElasticInterface(  # type: ignore[attr-defined]
        app.config["ELASTICSEARCH_URL"],
        app.config["ELASTIC_AUTH_ENABLE"],
        app.config["ELASTIC_USER"],
        app.config["ELASTIC_PASSWORD"],
    )

    login.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    scope_manager.init_app(app)
    app.config["webpack"] = webpack_manifest.load(
        # An absolute path to a manifest file
        path=os.path.join(
            app.config["BASEDIR"], "app", "static", "dist", "webpack_manifest.json"
        ),
        # The root url that your static assets are served from
        static_url="/static/",
    )

    with app.app_context():
        load_config_from_db(app, db)
        scope_manager.load_all_groups()

    register_converters(app)

    from app.cli.user import cli_group as user_cli

    app.cli.add_command(user_cli)

    from app.cli.scope import cli_group as scope_cli

    app.cli.add_command(scope_cli)

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


from app import models as models
