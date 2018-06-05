import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
	
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-should-set-a-secret-key'
	SCOPE_DOC = os.path.join(basedir, 'config/scope.txt')
	BLACKLIST_DOC = os.path.join(basedir, 'config/blacklist.txt')
	

	# Access Control Config
	LOGIN_REQUIRED = os.environ.get('LOGIN_REQUIRED')
	REGISTER_ALLOWED = os.environ.get('REGISTER_ALLOWED')

	# Display Config
	RESULTS_PER_PAGE = 100
	PREVIEW_LENGTH = 100

	# Data store config
	ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL') or \
		'http://localhost:9200'
	SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
		'sqlite:///' + os.path.join(basedir, 'metadata.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	
	# Mail Config
	MAIL_SERVER = os.environ.get('MAIL_SERVER')
	MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
	MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
	ADMINS=['dade@tutanota.com']