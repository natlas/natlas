import flask_migrate
import sqlalchemy
from alembic import context
from alembic.config import Config as alembic_cfg
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory


def migration_needed(sqlalchemy_uri):
    engine = sqlalchemy.create_engine(sqlalchemy_uri)
    conn = engine.connect()

    m_ctx = MigrationContext.configure(conn)
    cfg = alembic_cfg("migrations/alembic.ini")
    cfg.set_main_option("script_location", "migrations")
    scripts_dir = ScriptDirectory.from_config(cfg)
    with context.EnvironmentContext(cfg, scripts_dir):
        return context.get_head_revision() != m_ctx.get_current_revision()


def handle_db_upgrade(app):
    if app.config["DB_AUTO_UPGRADE"]:
        with app.app_context():
            print("upgrading")
            flask_migrate.upgrade()
            return True
    else:
        return False


def handle_db_downgrade(app):
    with app.app_context():
        print("downgrading")
        flask_migrate.downgrade()


def handle_db_migrate(app, message=""):
    with app.app_context():
        print("migrating")
        flask_migrate.migrate(message=message)
