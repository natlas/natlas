from app import create_app, db
from app.models import User, ScopeItem, ConfigItem

app = create_app(load_config=True)

@app.shell_context_processor
def make_shell_context():
	return {'db':db, 'User':User, 'ScopeItem':ScopeItem, 'ConfigItem':ConfigItem}
