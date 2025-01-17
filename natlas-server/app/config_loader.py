import sqlalchemy
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


def load_agent_scripts(app: Flask, db: SQLAlchemy) -> None:
    insp = sqlalchemy.inspect(db.engine)
    if not insp.has_table("agent_script"):
        return

    from app.models import AgentScript

    app.agent_scripts = AgentScript.get_scripts_string()  # type: ignore[attr-defined]


def load_config_from_db(app: Flask, db: SQLAlchemy) -> None:
    load_agent_scripts(app, db)
