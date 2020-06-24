import flask
import sentry_sdk
import threading
from opencensus.ext.ocagent import trace_exporter as ocagent_trace_exporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace import config_integration, samplers
from opencensus.trace import execution_context
from .sentryio_middleware import SentryIoContextMiddleware
from urllib.parse import urlparse


SERVICE_NAME = "natlas-server"
template_span = threading.local()


def render_template_end(*kargs, **kwargs):  # sender, template, context):
    span = template_span.x
    template_span.x = None
    span.__exit__(None, None, None)


def render_template_start(app, template, context):
    tracer = execution_context.get_opencensus_tracer()
    template_span.x = tracer.span(name="render_template")
    template_span.x.add_attribute("flask.template", template.name)


def initialize_opencensus(config, flask_app):
    if config.opencensus_enable:
        agent = config.opencensus_agent
        print(f"OpenCensus enabled and reporting to {agent} using gRPC")
        exporter = ocagent_trace_exporter.TraceExporter(
            service_name=SERVICE_NAME, endpoint=agent
        )
        sampler = samplers.ProbabilitySampler(rate=config.opencensus_sample_rate)
        config_integration.trace_integrations(["sqlalchemy"])
        FlaskMiddleware(flask_app, exporter=exporter, sampler=sampler)
        flask_app.wsgi_app = SentryIoContextMiddleware(flask_app.wsgi_app)

        flask.before_render_template.connect(render_template_start, flask_app)
        flask.template_rendered.connect(render_template_end, flask_app)


def initialize_sentryio(config):
    if config.sentry_dsn:
        url = urlparse(config.sentry_dsn)
        print(
            f"Sentry.io enabled and reporting errors to {url.scheme}://{url.hostname}"
        )
        from sentry_sdk.integrations.flask import FlaskIntegration

        sentry_sdk.init(
            dsn=config.sentry_dsn,
            release=config.NATLAS_VERSION,
            integrations=[FlaskIntegration()],
        )
