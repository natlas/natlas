import os
from dotenv import load_dotenv

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, '.env'))

class Config(object):
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-should-set-a-secret-key'

    # Access Control Config
    LOGIN_REQUIRED = os.environ.get('LOGIN_REQUIRED') or False
    REGISTER_ALLOWED = os.environ.get('REGISTER_ALLOWED') or False

    # Display Config
    if os.environ.get('RESULTS_PER_PAGE'):
        RESULTS_PER_PAGE = int(os.environ.get('RESULTS_PER_PAGE'))
    else:
        RESULTS_PER_PAGE = 100
    if os.environ.get('PREVIEW_LENGTH'):
        PREVIEW_LENGTH = int(os.environ.get('PREVIEW_LENGTH'))
    else:
        PREVIEW_LENGTH = 100
    PREFERRED_URL_SCHEME = 'https'

    # Data store config
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL') or \
        'http://localhost:9200'
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
        'sqlite:///' + os.path.join(BASEDIR, 'metadata.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail Config
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_FROM = os.environ.get('MAIL_FROM')
