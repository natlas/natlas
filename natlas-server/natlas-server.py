from app import create_app, db
from app.instrumentation import initialize_sentryio
from app.models import (
    Agent,
    AgentConfig,
    AgentScript,
    ConfigItem,
    NatlasServices,
    RescanTask,
    ScopeItem,
    ScopeLog,
    Tag,
    User,
    UserInvitation,
)
from config import Config
from sentry_sdk import capture_exception

config = Config()
initialize_sentryio(config)
try:
    app = create_app(config)
except Exception as e:
    capture_exception(e)
    raise


@app.shell_context_processor
def make_shell_context():  # type: ignore[no-untyped-def]
    return {
        "db": db,
        "User": User,
        "ScopeItem": ScopeItem,
        "ConfigItem": ConfigItem,
        "NatlasServices": NatlasServices,
        "AgentConfig": AgentConfig,
        "RescanTask": RescanTask,
        "Tag": Tag,
        "Agent": Agent,
        "AgentScript": AgentScript,
        "UserInvitation": UserInvitation,
        "ScopeLog": ScopeLog,
    }
