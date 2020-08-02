import config


def load_natlas_config(app, db):
    if not db.engine.has_table("config_item"):
        return

    from app.models import ConfigItem

    for item in ConfigItem.query.all():
        app.config[item.name] = config.casted_value(item.type, item.value)


def load_natlas_services(app, db):
    if not db.engine.has_table("natlas_services"):
        return
    from app.models import NatlasServices

    current_services = NatlasServices.query.order_by(NatlasServices.id.desc()).first()
    app.current_services = current_services.as_dict()


def load_agent_config(app, db):
    if not db.engine.has_table("agent_config"):
        return

    from app.models import AgentConfig

    # the agent config is updated in place so there's only ever 1 record
    app.agentConfig = AgentConfig.query.get(1).as_dict()


def load_agent_scripts(app, db):
    if not db.engine.has_table("agent_script"):
        return

    from app.models import AgentScript

    app.agentScripts = AgentScript.query.all()
    app.agentScriptStr = AgentScript.getScriptsString(scriptList=app.agentScripts)


def load_config_from_db(app, db):
    load_natlas_config(app, db)
    load_natlas_services(app, db)
    load_agent_config(app, db)
    load_agent_scripts(app, db)
