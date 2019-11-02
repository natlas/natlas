from urllib.parse import urlparse
import sentry_sdk


def initialize_sentryio(config):
	if config.sentry_dsn:
		url = urlparse(config.sentry_dsn)
		print("Sentry.io enabled and reporting errors to %s://%s" % (url.scheme, url.hostname))
		sentry_sdk.init(dsn=config.sentry_dsn, release=config.NATLAS_VERSION)
