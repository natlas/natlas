import os
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="natlas_")
    NATLAS_VERSION: str = "0.6.12"
    base_dir: str = os.path.abspath(os.path.dirname(__file__))
    server: str = Field(alias="natlas_server_address", default="http://127.0.0.1:5000")
    data_dir: str = Field(default="/data")
    ignore_ssl_warn: bool = Field(default=False)
    max_threads: int = Field(default=3)
    scan_local: bool = Field(default=False)
    request_timeout: int = Field(default=15)
    backoff_max: int = Field(default=300)
    backoff_base: int = Field(default=1)
    max_retries: int = Field(default=10)
    agent_id: str = Field(default="anonymous")
    auth_token: str | None = Field(alias="natlas_agent_token", default=None)
    save_fails: bool = Field(default=False)
    version_override: str | None = Field(default=None)
    sentry_dsn: str | None = Field(alias="sentry_dsn", default=None)

    @model_validator(mode="after")
    def override_version(self) -> Self:
        if self.version_override:
            self.NATLAS_VERSION = self.version_override
        return self
