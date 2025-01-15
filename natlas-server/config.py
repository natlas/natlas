import json
import os
import secrets
from typing import Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings

with open("defaults/db_configs.json") as f:
    defaultConfig = json.load(f)


def get_defaults():  # type: ignore[no-untyped-def]
    return defaultConfig.items()


# This mechanism for casting a bool is needed because bool("False") == True
def casted_bool(value):  # type: ignore[no-untyped-def]
    if isinstance(value, bool):
        return value
    return value.lower() == "true"


def casted_value(expected_type, value):  # type: ignore[no-untyped-def]
    cast_map = {"bool": casted_bool, "string": str, "int": int}
    return cast_map[expected_type](value)  # type: ignore[operator]


class BaseConfig:
    """Since settings are broken up into many classes, this makes it easy to repeat shared settings."""

    env_file_encoding = "utf-8"
    env_file = ".env"


class S3Settings(BaseSettings):
    endpoint: str
    bucket: str
    access_key: SecretStr
    secret_key: SecretStr
    use_tls: bool

    class Config(BaseConfig):
        env_prefix = "s3_"


class Config(BaseSettings):
    NATLAS_VERSION: str = "0.6.12"
    BASEDIR: str = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR: str = "/data"
    SERVER_NAME: str = Field(default="localhost:5000")
    SECRET_KEY: str = Field(default=secrets.token_urlsafe(64))
    PREFERRED_URL_SCHEME: str = Field(default="https")
    SQLALCHEMY_DATABASE_URI: str = Field(
        default=f"sqlite:///{os.path.join(DATA_DIR, 'db', 'metadata.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    DB_AUTO_UPGRADE: bool = Field(default=False)
    ELASTICSEARCH_URL: str = Field(default="http://localhost:9200")
    ELASTIC_AUTH_ENABLE: bool = Field(default=False)
    ELASTIC_USER: str = Field(default="elastic")
    ELASTIC_PASSWORD: str = Field(default="")

    MAIL_SERVER: str | None = Field(default=None)
    MAIL_PORT: int = Field(default=587)
    MAIL_USE_TLS: bool = Field(default=True)
    MAIL_USE_SSL: bool = Field(default=False)
    MAIL_USERNAME: str | None = Field(default=None)
    MAIL_PASSWORD: str | None = Field(default=None)
    MAIL_FROM: str | None = Field(default=None)

    CONSISTENT_SCAN_CYCLE: bool = Field(default=False)

    SENTRY_DSN: str | None = Field(default=None)
    SENTRY_JS_DSN: str | None = Field(default=None)
    OTEL_ENABLE: bool = Field(default=False)
    OTEL_COLLECTOR: str = Field(default="127.0.0.1:4317")

    version_override: str | None = Field(default=None)
    TESTING: bool = Field(default=False)

    # By capitalizing this, we can technically access this object from flask's app.config
    # I'm not certain I want to keep using flask's app.config or just move to using this config directly
    # But for now I'll maintain the pattern. `app.config['s3']` yields an S3Settings object.
    # Additionally, the settings load from environment, but mypy doesn't understand that.
    S3: S3Settings = S3Settings()  # type: ignore[call-arg]

    @model_validator(mode="after")
    def override_version(self) -> Self:
        if self.version_override:
            self.NATLAS_VERSION = self.version_override
        return self
