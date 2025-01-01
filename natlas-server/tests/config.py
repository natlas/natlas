from config import Config


class TestConfig(Config):

    # MAIL_FROM and MAIL_SERVER are required checks for delivering mail
    MAIL_FROM = "Test Mail <noreply@example.com>"
    MAIL_SERVER = "localhost"

    # Tell Flask that it's in testing mode
    TESTING = True

    # This uses an in-memory database.
    # It will not work with database migrations.
    # But will work if you just want an app instance with
    # an empty database via db.create_all()
    SQLALCHEMY_DATABASE_URI = "sqlite://"

    # By enabling this, we can test migrations automatically whenever the app is used
    DB_AUTO_UPGRADE = True

    # Assume that the test environment has access to elastic via localhost:9200
    ELASTICSEARCH_URL = "http://elastic:9200"
    ELASTIC_AUTH_ENABLE = True
    ELASTIC_USER = "elastic"
    ELASTIC_PASSWORD = "natlas-dev-password-do-not-use"
