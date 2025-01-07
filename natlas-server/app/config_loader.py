import config
import sqlalchemy
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


def load_natlas_config(app: Flask, db: SQLAlchemy) -> None:
    insp = sqlalchemy.inspect(db.engine)
    if not insp.has_table("config_item"):
        return

    from app.models import ConfigItem

    for item in db.session.execute(db.select(ConfigItem)).scalars().all():
        app.config[item.name] = config.casted_value(item.type, item.value)


def load_natlas_services(app: Flask, db: SQLAlchemy) -> None:
    insp = sqlalchemy.inspect(db.engine)
    if not insp.has_table("natlas_services"):
        return
    from app.models import NatlasServices

    app.current_services = NatlasServices.get_latest_services()  # type: ignore[attr-defined]


def load_agent_config(app: Flask, db: SQLAlchemy) -> None:
    insp = sqlalchemy.inspect(db.engine)
    if not insp.has_table("agent_config"):
        return

    from app.models import AgentConfig

    # the agent config is updated in place so there's only ever 1 record
    app.agentConfig = db.session.get(AgentConfig, 1).as_dict()  # type: ignore[attr-defined, union-attr]


def load_agent_scripts(app: Flask, db: SQLAlchemy) -> None:
    insp = sqlalchemy.inspect(db.engine)
    if not insp.has_table("agent_script"):
        return

    from app.models import AgentScript

    app.agent_scripts = AgentScript.get_scripts_string()  # type: ignore[attr-defined]


def load_config_from_db(app: Flask, db: SQLAlchemy) -> None:
    load_natlas_config(app, db)
    load_natlas_services(app, db)
    load_agent_config(app, db)
    load_agent_scripts(app, db)
