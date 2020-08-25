from alembic.migration import MigrationContext
from alembic import context
from alembic.config import Config as alembic_cfg
from alembic.script import ScriptDirectory
import flask_migrate
from sqlalchemy import create_engine


def migration_needed(sqlalchemy_uri):
    engine = create_engine(sqlalchemy_uri)
    conn = engine.connect()
    m_ctx = MigrationContext.configure(conn)
    cfg = alembic_cfg("migrations/alembic.ini")
    cfg.set_main_option("script_location", "migrations")
    scripts_dir = ScriptDirectory.from_config(cfg)
    with context.EnvironmentContext(cfg, scripts_dir):
        print(f"{context.get_head_revision()} =? {m_ctx.get_current_revision()}")
        return context.get_head_revision() != m_ctx.get_current_revision()


def handle_db_migration(app):
    if app.config["DB_AUTO_MIGRATE"]:
        with app.app_context():
            flask_migrate.upgrade()
            return True
    else:
        return False
