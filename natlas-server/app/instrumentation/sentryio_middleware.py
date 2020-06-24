from sentry_sdk import configure_scope
from opencensus.trace import execution_context


class SentryIoContextMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        tracer = execution_context.get_opencensus_tracer()
        with configure_scope() as scope:
            scope.set_extra("trace_id", tracer.span_context.trace_id)
            return self.app(environ, start_response)
