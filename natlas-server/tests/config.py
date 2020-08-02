from config import Config


class TestConfig(Config):
    MAIL_FROM = "Test Mail <noreply@example.com>"
    MAIL_SERVER = "localhost"
    TESTING = True
    # This uses an in-memory database
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    DB_AUTO_MIGRATE = True
    ELASTICSEARCH_URL = "http://localhost:9200"
