import os
import secrets
import json
from dotenv import load_dotenv

with open("defaults/db_configs.json", "r") as f:
    defaultConfig = json.load(f)


def get_defaults():
    return defaultConfig.items()


# This mechanism for casting a bool is needed because bool("False") == True
def casted_bool(value):
    if isinstance(value, bool):
        return value
    return value.lower() == "true"


def casted_value(expected_type, value):
    cast_map = {"bool": casted_bool, "string": str, "int": int}
    return cast_map[expected_type](value)


# Things in the Class object are config options we will likely never want to change from the database.
class Config(object):

    # Current Version
    NATLAS_VERSION = "0.6.10"

    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(BASEDIR, ".env"))

    # Leaving this empty will work fine for requests but scripts won't be able to generate links
    # Examples: localhost:5000, natlas.io
    SERVER_NAME = os.environ.get("SERVER_NAME", None)

    # We aren't storing this in the database because it wouldn't be a very good secret then
    # If a key is not provided, generate a new one when the application starts
    SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_urlsafe(64))

    # Optionally generate links with http instead of https by overriding this value
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "https")

    # This isn't in the database because this is where we find the database.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///" + os.path.join(BASEDIR, "metadata.db")
    )

    # This isn't in the database because we'll never want to change it
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # This isn't in the database because it really shouldn't be changing on-the-fly
    # Also make sure that you're using an absolute path if you're serving your app directly via flask
    MEDIA_DIRECTORY = os.environ.get("MEDIA_DIRECTORY", os.path.join(BASEDIR, "media/"))

    # Elasticsearch only gets loaded from environment
    ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")

    # MAIL SETTINGS
    MAIL_SERVER = os.environ.get("MAIL_SERVER", None)
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = casted_bool(os.environ.get("MAIL_USE_TLS", False))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", None)
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", None)
    MAIL_FROM = os.environ.get("MAIL_FROM", None)

    # Scan Cycle option(s)
    CONSISTENT_SCAN_CYCLE = casted_bool(os.environ.get("CONSISTENT_SCAN_CYCLE", False))

    # Allow version overrides for local development
    # Necessary to test versioned host data templates before release
    version_override = os.environ.get("NATLAS_VERSION_OVERRIDE", None)

    # Replace NATLAS_VERSION so that the rest of the code doesn't have to care if it's being overridden
    if version_override:
        NATLAS_VERSION = version_override

    # Instrumentation isn't directly used by the flask app context so does not need to be ALL_CAPS
    sentry_dsn = os.environ.get("SENTRY_DSN", None)
    SENTRY_JS_DSN = os.environ.get("SENTRY_JS_DSN", None)
    opencensus_enable = casted_bool(os.environ.get("OPENCENSUS_ENABLE", False))
    opencensus_sample_rate = float(os.environ.get("OPENCENSUS_SAMPLE_RATE", 1))
    opencensus_agent = os.environ.get("OPENCENSUS_AGENT", "127.0.0.1:55678")
