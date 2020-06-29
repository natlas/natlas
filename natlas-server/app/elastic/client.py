import json
from config import Config
import elasticsearch
import time
from datetime import datetime
import logging
from opencensus.trace import execution_context
from opencensus.trace import span as span_module
import semver


class ElasticClient:
    es = None
    lastReconnectAttempt = None
    mapping = {}
    natlasIndices = ["nmap", "nmap_history"]
    status = False
    # Quiets the elasticsearch logger because otherwise connection errors print tracebacks to the WARNING level, even when the exception is handled.
    logger = logging.getLogger("elasticsearch")
    logger.setLevel("ERROR")

    def __init__(self, elasticURL):
        # Elastic is initialized outside an application context so we have to instatiate Config ourselves to get BASEDIR
        with open(Config().BASEDIR + "/defaults/elastic/mapping.json") as mapfile:
            self.mapping = json.loads(mapfile.read())
        try:
            self.es = elasticsearch.Elasticsearch(elasticURL, timeout=5, max_retries=1)
            self.status = self._ping()
            if self.status:
                self.esversion = semver.VersionInfo.parse(
                    self.es.info()["version"]["number"]
                )
                self.logger.info("Elastic Version: " + str(self.esversion))

                self._initialize_indices()
                self.logger.info("Initialized Elasticsearch indices")
        except Exception:
            self.status = False
            raise
        finally:
            # Set the lastReconnectAttempt to the timestamp after initialization
            self.lastReconnectAttempt = datetime.utcnow()
        return

    def _initialize_indices(self):
        """ Check each required index and make sure it exists, if it doesn't then create it """
        for index in self.natlasIndices:
            if not self.es.indices.exists(index):
                self.es.indices.create(index)

        # Avoid a race condition
        time.sleep(2)

        for index in self.natlasIndices:
            if self.esversion.match("<7.0.0"):
                self.es.indices.put_mapping(
                    index=index,
                    doc_type="_doc",
                    body=self.mapping,
                    include_type_name=True,
                )
            else:
                self.es.indices.put_mapping(
                    index=index,
                    body=self.mapping
                )

    def _ping(self):
        """ Returns True if the cluster is up, False otherwise"""
        with self._new_trace_span(operation="ping"):
            return self.es.ping()

    def _attempt_reconnect(self):
        """ Attempt to reconnect if we haven't tried to reconnect too recently """
        now = datetime.utcnow()
        delta = now - self.lastReconnectAttempt
        if delta.seconds >= 30:
            self.status = self._ping()

        return self.status

    def _check_status(self):
        """ If we're in a known bad state, try to reconnect """
        if not (self.status or self._attempt_reconnect()):
            raise elasticsearch.ConnectionError
        return self.status

    def get_collection(self, **kwargs):
        """ Execute a search and return a collection of results """
        results = self.execute_search(**kwargs)
        if not results:
            return 0, []
        docsources = self.collate_source(results["hits"]["hits"])
        return results["hits"]["total"], docsources

    def get_single_host(self, **kwargs):
        """ Execute a search and return a single result """
        results = self.execute_search(**kwargs)
        if not results or results["hits"]["total"] == 0:
            return 0, None
        return results["hits"]["total"], results["hits"]["hits"][0]["_source"]

    def collate_source(self, documents):
        return map(lambda doc: doc["_source"], documents)

    # Mid-level query executor abstraction.
    def execute_search(self, **kwargs):
        """ Execute an arbitrary search."""
        with self._new_trace_span(operation="search", **kwargs) as span:
            results = self._execute_raw_query(
                self.es.search, doc_type="_doc", rest_total_hits_as_int=True, **kwargs
            )
            span.add_attribute("es.hits.total", results["hits"]["total"])
            self._attach_shard_span_attrs(span, results)
            return results

    def execute_count(self, **kwargs):
        """ Executes an arbitrary count."""
        results = None
        with self._new_trace_span(operation="count", **kwargs) as span:
            results = self._execute_raw_query(self.es.count, doc_type="_doc", **kwargs)
            self._attach_shard_span_attrs(span, results)
        if not results:
            return 0
        return results

    def execute_delete_by_query(self, **kwargs):
        """ Executes an arbitrary delete_by_query."""
        with self._new_trace_span(operation="delete_by", **kwargs):
            results = self._execute_raw_query(
                self.es.delete_by_query, doc_type="_doc", **kwargs
            )
            return results

    def execute_index(self, **kwargs):
        """ Executes an arbitrary index. """
        with self._new_trace_span(operation="index", **kwargs):
            return self._execute_raw_query(self.es.index, doc_type="_doc", **kwargs)

    # Inner-most query executor. All queries route through here.
    def _execute_raw_query(self, func, **kwargs):
        """ Wraps the es client to make sure that ConnectionErrors are handled uniformly """
        self._check_status()
        try:
            return func(**kwargs)
        except elasticsearch.ConnectionError:
            self.status = False
            raise elasticsearch.ConnectionError

    # Tracing methods
    def _new_trace_span(self, operation, **kwargs):
        tracer = execution_context.get_opencensus_tracer()
        span_name = "elasticsearch"
        if "index" in kwargs:
            span_name += "." + operation
        span = tracer.span(name=span_name)
        span.span_kind = span_module.SpanKind.CLIENT
        if "index" in kwargs:
            span.add_attribute("es.index", kwargs["index"])
        if "body" in kwargs:
            span.add_attribute("es.query", kwargs["body"])
        return span

    def _attach_shard_span_attrs(self, span, results):
        span.add_attribute("es.shards.total", results["_shards"]["total"])
        span.add_attribute("es.shards.successful", results["_shards"]["successful"])
