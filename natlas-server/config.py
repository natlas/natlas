import argparse
import os
import secrets
import json
from dotenv import load_dotenv


# Things in the Class object are config options we will likely never want to change from the database.
class Config(object):

	# Current Version
	NATLAS_VERSION = "0.6.10"

	BASEDIR = os.path.abspath(os.path.dirname(__file__))
	load_dotenv(os.path.join(BASEDIR, '.env'))

	# Leaving this empty will work fine for requests but scripts won't be able to generate links
	# Examples: localhost:5000, natlas.io
	SERVER_NAME = os.environ.get('SERVER_NAME', None)

	# We aren't storing this in the database because it wouldn't be a very good secret then
	# If a key is not provided, generate a new one when the application starts
	SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_urlsafe(64))

	# Optionally generate links with http instead of https by overriding this value
	PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'https')

	# This isn't in the database because this is where we find the database.
	SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + os.path.join(BASEDIR, 'metadata.db'))

	# This isn't in the database because we'll never want to change it
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	# This isn't in the database because it really shouldn't be changing on-the-fly
	# Also make sure that you're using an absolute path if you're serving your app directly via flask
	MEDIA_DIRECTORY = os.environ.get('MEDIA_DIRECTORY', os.path.join(BASEDIR, 'media/'))

	# Elasticsearch only gets loaded from environment
	ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')

	# MAIL SETTINGS
	MAIL_SERVER = os.environ.get('MAIL_SERVER', None)
	MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
	MAIL_USE_TLS = bool(os.environ.get('MAIL_USE_TLS', False))
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME', None)
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', None)
	MAIL_FROM = os.environ.get('MAIL_FROM', None)

	# Allow version overrides for local development
	# Necessary to test versioned host data templates before release
	version_override = os.environ.get("NATLAS_VERSION_OVERRIDE", None)

	# Replace NATLAS_VERSION so that the rest of the code doesn't have to care if it's being overridden
	if version_override:
		NATLAS_VERSION = version_override

	# Instrumentation isn't directly used by the flask app context so does not need to be ALL_CAPS
	sentry_dsn = os.environ.get("SENTRY_DSN", None)
	opencensus_enable = os.environ.get("OPENCENSUS_ENABLE", False)
	opencensus_sample_rate = float(os.environ.get("OPENCENSUS_SAMPLE_RATE", 1))
	opencensus_agent = os.environ.get("OPENCENSUS_AGENT", '127.0.0.1:55678')


# NAME, TYPE, DEFAULT
defaultConfig = json.load(open('defaults/db_configs.json', 'r'))


def get_defaults():
	return defaultConfig


def casted_value(type, value):
	if type == "bool":
		if value.lower() == "true":
			return True
		else:
			return False
	elif type == "string":
		return str(value)
	elif type == "int":
		return int(value)
	else:
		return None


def get_current_config():
	from app import create_app
	from app.models import ConfigItem
	app = create_app(load_config=False)
	with app.app_context():
		for item in ConfigItem.query.all():
			print("%s, %s, %s" % (item.name, item.type, item.value))


# run as standalone to populate the config items into the database using environment or default values
def populate_defaults(verbose=False):

	from app import create_app, db
	from app.models import ConfigItem
	app = create_app(load_config=False)
	with app.app_context():
		for item in defaultConfig:
			conf = ConfigItem.query.filter_by(name=item[0]).first()
			if conf:
				conf.type = item[1]
				conf.value = os.environ.get(item[0]) or item[2]
				if verbose:
					print("[+] Item named %s already existed. Setting type to '%s' and value to '%s'" % (item[0], item[1], conf.value))
			else:
				if verbose:
					print("[+] Adding config item named '%s', of type '%s', with value '%s'." % (item[0], item[1], item[2]))
				conf = ConfigItem(name=item[0], type=item[1], value=os.environ.get(item[0]) or item[2])
			db.session.add(conf)
		print("[+] Committing config changes to database")
		db.session.commit()


def main():
	parser_desc = '''
	Utility for initially populating the database from the environment. Flask will automatically try to populate the database if no config items are found.
	Only run this if you want to reset the config settings to default or to environment variables.
	'''
	parser_epil = "Be sure that you're running this from within the virtual environment for the server."
	parser = argparse.ArgumentParser(description=parser_desc, epilog=parser_epil)
	parser.add_argument("--populate", action="store_true", default=False)
	parser.add_argument("-v", "--verbose", action="store_true", default=False)
	args = parser.parse_args()
	if args.populate:
		populate_defaults(args.verbose)
	else:
		print("[+] Getting current config from database\nNAME, TYPE, VALUE")
		get_current_config()


if __name__ == "__main__":
	main()
