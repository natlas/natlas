import elasticsearch
import time
from datetime import datetime, UTC
import logging
from opentelemetry import trace
import semver


class ElasticClient:
    es = None
    lastReconnectAttempt = None
    mapping = {}
    status = False
    # Quiets the elasticsearch logger because otherwise connection errors print tracebacks to the WARNING level, even when the exception is handled.
    logger = logging.getLogger("elasticsearch")
    logger.setLevel("ERROR")

    def __init__(self, elasticURL: str, authEnabled: bool, elasticUser: str, elasticPassword: str):
        try:
            if authEnabled:
                self.es = elasticsearch.Elasticsearch(elasticURL,
                                                      timeout=5,
                                                      max_retries=1,
                                                      http_auth=(elasticUser, elasticPassword))
            else:
                self.es = elasticsearch.Elasticsearch(elasticURL, timeout=5, max_retries=1)
            self.status = self._ping()
            if self.status:
                self.esversion = semver.VersionInfo.parse(
                    self.es.info()["version"]["number"]
                )
                self.logger.info("Elastic Version: " + str(self.esversion))
        except Exception:
            self.status = False
            raise
        finally:
            # Set the lastReconnectAttempt to the timestamp after initialization
            self.lastReconnectAttempt = datetime.now(UTC)

    def _ping(self):
        """
            Returns True if the cluster is up, False otherwise
        """
        with self._new_trace_span(operation="ping"):
            return self.es.ping()

    def _attempt_reconnect(self):
        """
            Attempt to reconnect if we haven't tried to reconnect too recently
        """
        now = datetime.now(UTC)
        delta = now - self.lastReconnectAttempt
        if delta.seconds >= 30:
            self.status = self._ping()
            self.lastReconnectAttempt = now

        return self.status

    def _check_status(self):
        """
            If we're in a known bad state, try to reconnect
        """
        if not (self.status or self._attempt_reconnect()):
            raise elasticsearch.ConnectionError("Could not connect to Elasticsearch")
        return self.status

    def set_auth(self, elasticUser: str, elasticPassword: str):
        self.es.options(basic_auth=(elasticUser, elasticPassword))

    def initialize_index(self, index: str, mapping: dict):
        """
            Check each required index and make sure it exists, if it doesn't then create it
        """
        with self._new_trace_span(operation="initialize_index"):
            if not self.es.indices.exists(index=index):
                self.es.indices.create(index=index)

            time.sleep(1)

            if self.esversion.match("<7.0.0"):
                self.es.indices.put_mapping(
                    index=index, doc_type="_doc", body=mapping, include_type_name=True
                )
            else:
                self.es.indices.put_mapping(index=index, body=mapping)

    def delete_index(self, index: str):
        """
            Delete an existing index
        """
        if self.es.indices.exists(index=index):
            self.es.indices.delete(index=index)

    def index_exists(self, index: str):
        """
            Check if index exists
        """
        return self.es.indices.exists(index=index)

    def get_collection(self, **kwargs):
        """
            Execute a search and return a collection of results
        """
        results = self.execute_search(**kwargs)
        if not results:
            return 0, []
        docsources = self.collate_source(results["hits"]["hits"])
        return results["hits"]["total"], docsources

    def get_single_host(self, **kwargs):
        """
            Execute a search and return a single result
        """
        results = self.execute_search(**kwargs)
        if not results or results["hits"]["total"] == 0:
            return 0, None
        return results["hits"]["total"], results["hits"]["hits"][0]["_source"]

    def collate_source(self, documents):
        return list(map(lambda doc: doc["_source"], documents))

    # Mid-level query executor abstraction.
    def execute_search(self, **kwargs):
        """
            Execute an arbitrary search.
        """
        with self._new_trace_span(operation="search", **kwargs) as span:
            results = self._execute_raw_query(
                self.es.search, rest_total_hits_as_int=True, **kwargs
            )
            span.set_attribute("es.hits.total", results["hits"]["total"])
            self._attach_shard_span_attrs(span, results)
            return results

    def execute_count(self, **kwargs):
        """
            Executes an arbitrary count.
        """
        results = None
        with self._new_trace_span(operation="count", **kwargs) as span:
            results = self._execute_raw_query(self.es.count, **kwargs)
            self._attach_shard_span_attrs(span, results)
        if not results:
            return 0
        return results

    def execute_delete_by_query(self, **kwargs):
        """
            Executes an arbitrary delete_by_query.
        """
        with self._new_trace_span(operation="delete_by", **kwargs):
            return self._execute_raw_query(
                self.es.delete_by_query, **kwargs
            )

    def execute_index(self, **kwargs):
        """
            Executes an arbitrary index.
        """
        with self._new_trace_span(operation="index", **kwargs):
            return self._execute_raw_query(self.es.index, **kwargs)

    # Inner-most query executor. All queries route through here.
    def _execute_raw_query(self, func: callable, **kwargs):
        """
            Wraps the es client to make sure that ConnectionErrors are handled uniformly
        """
        self._check_status()
        try:
            return func(**kwargs)
        except elasticsearch.ConnectionError:
            self.status = False
            raise

    # Tracing methods
    def _new_trace_span(self, operation: str, **kwargs):
        tracer = trace.get_tracer(__name__)
        span_name = "elasticsearch"
        if "index" in kwargs:
            span_name += "." + operation
        span = tracer.start_span(name=span_name)
        if "index" in kwargs:
            span.set_attribute("es.index", f'{kwargs["index"]}')
        if "body" in kwargs:
            span.set_attribute("es.query", f'{kwargs["body"]}')
        return span

    def _attach_shard_span_attrs(self, span, results: dict):
        span.set_attribute("es.shards.total", results["_shards"]["total"])
        span.set_attribute("es.shards.successful", results["_shards"]["successful"])
