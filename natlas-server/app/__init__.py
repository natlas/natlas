from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, AnonymousUserMixin
from flask_mail import Mail
from config import Config, populate_defaults
from app.elastic import Elastic
from app.scope import ScopeManager
import sqlalchemy
import os

class AnonUser(AnonymousUserMixin):

    results_per_page = 50
    preview_length = 50


login = LoginManager()
login.login_view = 'auth.login'
login.anonymous_user = AnonUser
login.login_message_category = "warning"
login.session_protection = "strong"
mail = Mail()
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config, load_config=False):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.jinja_env.add_extension('jinja2.ext.do')

    db.init_app(app)
    migrate.init_app(app,db)
    login.init_app(app)
    mail.init_app(app)

    if load_config:
        print("Loading Config from database")
        with app.app_context():
            from app.models import ConfigItem
            try: # This is gross but we need it because otherwise flask db operations won't work to create the ConfigItem table in the first place.
                conf = ConfigItem.query.all()
                if not conf: # We'll hit this if the table exists but there's no data
                    populate_defaults(verbose=False)
                    conf = ConfigItem.query.all() # populate_defaults should populate data that we can query now
                    if not conf: # if it didn't, then we don't have config items that we need in order to run, so exit.
                        raise(SystemExit())
                
                for item in conf:
                    if item.type == "int":
                        app.config[item.name] = int(item.value)
                    elif item.type == "bool":
                        if item.value == "True":
                            app.config[item.name] = True
                        else:
                            app.config[item.name] = False
                    elif item.type == "string":
                        app.config[item.name] = item.value
                    else:
                        print("Unsupported config type %s:%s:%s" % (item.name, item.type, item.value))
            except Exception as e:
                print("ConfigItem table doesn't exist yet. Ignore this if you're running flask db upgrade right now.")
            
            from app.models import NatlasServices
            try:
                current_services = NatlasServices.query.order_by(NatlasServices.id.desc()).first()
                if current_services:
                    app.current_services = current_services.as_dict()
                else:
                    app.current_services = {"id":"None","sha256":"None","services":"None"} # default values until we load something
            except Exception as e:
                print("NatlasServices table probably doesn't exist yet. Ignore if you're running flask db upgrade.")
        
        # Grungy thing so we can use flask db and flask shell before the config items are initially populated
        if "ELASTICSEARCH_URL" in app.config: 
            app.elastic = Elastic(app.config['ELASTICSEARCH_URL'])

    app.ScopeManager = ScopeManager()

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.filters import bp as filters_bp
    app.register_blueprint(filters_bp)

    return app

from app import models