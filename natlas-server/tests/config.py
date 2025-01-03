from config import Config

test_config = Config(
    MAIL_FROM="Test Mail <noreply@example.com>",
    MAIL_SERVER="localhost",
    TESTING=True,
    SQLALCHEMY_DATABASE_URI="sqlite://",
    DB_AUTO_UPGRADE=True,
    ELASTICSEARCH_URL="http://elastic:9200",
    ELASTIC_AUTH_ENABLE=True,
    ELASTIC_USER="elastic",
    ELASTIC_PASSWORD="natlas-dev-password-do-not-use",
)
