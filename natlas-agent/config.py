import os
from typing import Self

from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class LegacyConfig:
    # Current Version
    NATLAS_VERSION = "0.6.12"

    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(BASEDIR, ".env"))

    def get_int(self, varname: str) -> int | None:
        return int(tmp) if (tmp := os.environ.get(varname)) else None

    def get_bool(self, varname: str) -> bool | None:
        tmp = os.environ.get(varname)
        if tmp and tmp.upper() == "TRUE":
            return True
        if tmp and tmp.upper() == "FALSE":
            return False
        return None

    def __init__(self):  # type: ignore[no-untyped-def]
        # url of server to get/submit work from/to
        self.server = os.environ.get("NATLAS_SERVER_ADDRESS") or "http://127.0.0.1:5000"

        # Location of data directory
        self.data_dir = os.environ.get("NATLAS_DATA_DIR", "/data")

        # ignore warnings about SSL connections
        # you shouldn't ignore ssl warnings, but I'll give you the option
        # Instead, you should put the trusted CA certificate bundle on the agent and use the REQUESTS_CA_BUNDLE env variable
        self.ignore_ssl_warn = self.get_bool("NATLAS_IGNORE_SSL_WARN") or False

        # maximum number of threads to utilize
        self.max_threads = self.get_int("NATLAS_MAX_THREADS") or 3

        # Are we allowed to scan local addresses?
        # By default, agents protect themselves from scanning their local network
        self.scan_local = self.get_bool("NATLAS_SCAN_LOCAL") or False

        # default time to wait for the server to respond
        self.request_timeout = self.get_int("NATLAS_REQUEST_TIMEOUT") or 15  # seconds

        # Maximum value for exponential backoff of requests, 5 minutes default
        self.backoff_max = self.get_int("NATLAS_BACKOFF_MAX") or 300  # seconds

        # Base value to begin the exponential backoff
        self.backoff_base = self.get_int("NATLAS_BACKOFF_BASE") or 1  # seconds

        # Maximum number of times to retry submitting data before giving up
        # This is useful if a thread is submitting data that the server doesn't understand for some reason
        self.max_retries = self.get_int("NATLAS_MAX_RETRIES") or 10

        # Identification string that identifies the agent that performed any given scan
        # Used for database lookup and stored in scan output
        self.agent_id = os.environ.get("NATLAS_AGENT_ID") or None

        # Authentication token that agents can use to talk to the server API
        # Only needed if the server is configured to require agent authentication
        self.auth_token = os.environ.get("NATLAS_AGENT_TOKEN") or None

        # Optionally save files that failed to upload
        self.save_fails = self.get_bool("NATLAS_SAVE_FAILS") or False

        # Allow version overrides for local development
        # Necessary to test versioned host data templates before release
        self.version_override = os.environ.get("NATLAS_VERSION_OVERRIDE") or None

        self.sentry_dsn = os.environ.get("SENTRY_DSN") or None

        if self.version_override:
            self.NATLAS_VERSION = self.version_override


class Config(BaseSettings):
    NATLAS_VERSION: str = "0.6.12"
    base_dir: str = os.path.abspath(os.path.dirname(__file__))
    server: str = Field(alias="natlas_server_address", default="http://127.0.0.1:5000")
    data_dir: str = Field(alias="natlas_data_dir", default="/data")
    ignore_ssl_warn: bool = Field(alias="natlas_ignore_ssl_warn", default=False)
    max_threads: int = Field(alias="natlas_max_threads", default=3)
    scan_local: bool = Field(alias="natlas_scan_local", default=False)
    request_timeout: int = Field(alias="natlas_request_timeout", default=15)
    backoff_max: int = Field(alias="natlas_backoff_max", default=300)
    backoff_base: int = Field(alias="natlas_backoff_base", default=1)
    max_retries: int = Field(alias="natlas_max_retries", default=10)
    agent_id: str = Field(alias="natlas_agent_id", default="anonymous")
    auth_token: str | None = Field(alias="natlas_agent_token", default=None)
    save_fails: bool = Field(alias="natlas_save_fails", default=False)
    version_override: str | None = Field(alias="natlas_version_override", default=None)
    sentry_dsn: str | None = Field(alias="sentry_dsn", default=None)

    @model_validator(mode="after")
    def override_version(self) -> Self:
        if self.version_override:
            self.NATLAS_VERSION = self.version_override
        return self
