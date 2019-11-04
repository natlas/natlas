from flask import current_app, request
from flask_login import current_user
from app import login as lm
from app.models import Agent
import json
from functools import wraps


def isAuthenticated(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if current_app.config['LOGIN_REQUIRED'] and not current_user.is_authenticated:
			return lm.unauthorized()
		return f(*args, **kwargs)
	return decorated_function


def isAdmin(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if current_user.is_anonymous or not current_user.is_admin:
			return lm.unauthorized()
		return f(*args, **kwargs)
	return decorated_function


def isAgentAuthenticated(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if current_app.config['AGENT_AUTHENTICATION']:
			if 'Authorization' not in request.headers:
				return json.dumps({'status': 403, 'message': 'Authorization is required to access this endpoint', 'retry': False}), \
					403, {'Content-Type': 'application/json'}
			authz = request.headers["Authorization"].split()
			if authz[0].lower() != "bearer":
				return json.dumps({'status': 403, 'message': 'Authorization is required to access this endpoint', 'retry': False}), \
					403, {'Content-Type': 'application/json'}
			agent_id = authz[1].split(':', 1)[0]
			agent_token = authz[1].split(":", 1)[1]
			agent = Agent.load_agent(agent_id)
			if not agent or not agent.verify_token(agent_token):
				return json.dumps({'status': 403, 'message': 'Authorization is required to access this endpoint', 'retry': False}), \
					403, {'Content-Type': 'application/json'}
		return f(*args, **kwargs)
	return decorated_function
