import argparse
import os
from dotenv import load_dotenv


# Things in the Class object are config options we will likely never want to change from the database.
class Config(object):

	# Current Version
	NATLAS_VERSION = "0.6.7"

	BASEDIR = os.path.abspath(os.path.dirname(__file__))
	load_dotenv(os.path.join(BASEDIR, '.env'))

	# We aren't storing this in the database because it wouldn't be a very good secret then
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-should-set-a-secret-key'

	# This isn't in the database because it doesn't _really_ matter.
	PREFERRED_URL_SCHEME = 'https'

	# This isn't in the database because this is where we find the database.
	SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
		'sqlite:///' + os.path.join(BASEDIR, 'metadata.db')

	# This isn't in the database because we'll never want to change it
	SQLALCHEMY_TRACK_MODIFICATIONS = False

	# This isn't in the database because it really shouldn't be changing on-the-fly
	# Also make sure that you're using an absolute path if you're serving your app directly via flask
	MEDIA_DIRECTORY = os.environ.get('MEDIA_DIRECTORY') or os.path.join(BASEDIR, 'media/')

	# Elasticsearch only gets loaded from environment
	ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL') or 'http://localhost:9200'

	# Allow version overrides for local development
	# Necessary to test versioned host data templates before release
	version_override = os.environ.get("NATLAS_VERSION_OVERRIDE") or None

	sentry_dsn = os.environ.get("SENTRY_DSN") or None

	opencensus_enable = os.environ.get("OPENCENSUS_ENABLE") or False
	opencensus_sample_rate = float(os.environ.get("OPENCENSUS_SAMPLE_RATE") or 1)
	opencensus_agent = os.environ.get("OPENCENSUS_AGENT") or '127.0.0.1:55678'

	if version_override:
		NATLAS_VERSION = version_override


# NAME, TYPE, DEFAULT
defaultConfig = [
	("LOGIN_REQUIRED", "bool", "False"),
	("REGISTER_ALLOWED", "bool", "False"),
	("AGENT_AUTHENTICATION", "bool", "False"),
	("MAIL_SERVER", "string", "localhost"),
	("MAIL_PORT", "int", "25"),
	("MAIL_USE_TLS", "bool", "False"),
	("MAIL_USERNAME", "string", ""),
	("MAIL_PASSWORD", "string", ""),
	("MAIL_FROM", "string", ""),
	("LOCAL_SUBRESOURCES", "bool", "False"),
	("CUSTOM_BRAND", "string", "")
]


def get_defaults():
	return defaultConfig


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
