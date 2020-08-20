from urllib.parse import urlparse
import sentry_sdk
from config import Config


def initialize_sentryio(config: Config):
    if config.sentry_dsn:
        url = urlparse(config.sentry_dsn)
        print(
            f"Sentry.io enabled and reporting errors to {url.scheme}://{url.hostname}"
        )
        sentry_sdk.init(dsn=config.sentry_dsn, release=config.NATLAS_VERSION)
