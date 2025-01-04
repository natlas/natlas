import threading
from urllib.parse import urlparse

import flask
import sentry_sdk
from config import Config
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.instrumentation.sentryio_middleware import SentryIoContextMiddleware

SERVICE_NAME = "natlas-server"
template_span = threading.local()


def render_template_end(*args: object, **kwargs: object) -> None:
    span = template_span.x
    template_span.x = None
    span.end()


def render_template_start(app: flask.Flask, template, context):  # type: ignore[no-untyped-def]
    tracer = trace.get_tracer(__name__)
    template_span.x = tracer.start_span(name="render_template")
    template_span.x.set_attribute("flask.template", template.name)


def initialize_opentelemetry(config: Config, flask_app: flask.Flask) -> None:
    if config.otel_enable:
        collector = config.otel_collector
        print(f"OpenTelemetry enabled and reporting to {collector} using gRPC")
        exporter = OTLPSpanExporter(endpoint=collector, insecure=True)
        provider = TracerProvider(
            resource=Resource.create({"service.name": SERVICE_NAME})
        )
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        flask_app.wsgi_app = SentryIoContextMiddleware(flask_app.wsgi_app)  # type: ignore[method-assign]
        FlaskInstrumentor().instrument_app(flask_app)
        flask.before_render_template.connect(render_template_start, flask_app)
        flask.template_rendered.connect(render_template_end, flask_app)


def initialize_sentryio(config: Config) -> None:
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
