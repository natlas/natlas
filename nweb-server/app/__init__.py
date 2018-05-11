from flask import Flask
from config import Config
from app.models import Elastic

app = Flask(__name__)
app.config.from_object(Config)
app.jinja_env.add_extension('jinja2.ext.do')
elastic = Elastic(app.config['ELASTICSEARCH_URL'])

from app import routes, models