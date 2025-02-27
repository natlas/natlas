from opentelemetry import trace
from sentry_sdk import configure_scope


class SentryIoContextMiddleware:
    def __init__(self, app):  # type: ignore[no-untyped-def]
        self.app = app

    def __call__(self, environ, start_response):  # type: ignore[no-untyped-def]
        span = trace.get_current_span()
        with configure_scope() as scope:
            scope.set_extra("trace_id", span.get_span_context().trace_id)
            return self.app(environ, start_response)
