from flask import current_app
from flask_login import current_user
from app import login as lm

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
        if not current_user.is_admin:
            return lm.unauthorized()
        return f(*args, **kwargs)
    return decorated_function