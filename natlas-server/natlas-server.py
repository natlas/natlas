from app import create_app, db
from app.models import User, ScopeItem, ConfigItem, NatlasServices, AgentConfig, RescanTask, \
	Tag, Agent, AgentScript, EmailToken, ScopeLog
from app.instrumentation import initialize_sentryio
from sentry_sdk import capture_exception
from config import Config


config = Config()
initialize_sentryio(config)
try:
	app = create_app(config_class=config, load_config=True)
except Exception as e:
	capture_exception(e)
	raise e


@app.shell_context_processor
def make_shell_context():
	return {
		'db': db,
		'User': User,
		'ScopeItem': ScopeItem,
		'ConfigItem': ConfigItem,
		'NatlasServices': NatlasServices,
		'AgentConfig': AgentConfig,
		'RescanTask': RescanTask,
		'Tag': Tag,
		'Agent': Agent,
		'AgentScript': AgentScript,
		'EmailToken': EmailToken,
		'ScopeLog': ScopeLog
	}
