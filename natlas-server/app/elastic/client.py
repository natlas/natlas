import json
from config import Config
import elasticsearch
from datetime import datetime
import logging


class ElasticClient:
	es = None
	lastReconnectAttempt = None
	mapping = {}
	natlasIndices = ["nmap", "nmap_history"]
	status = False
	# Quiets the elasticsearch logger because otherwise connection errors print tracebacks to the WARNING level, even when the exception is handled.
	logger = logging.getLogger('elasticsearch')
	logger.setLevel('ERROR')

	def __init__(self, elasticURL):
		# Elastic is initialized outside an application context so we have to instatiate Config ourselves to get BASEDIR
		with open(Config().BASEDIR + '/defaults/elastic/mapping.json') as mapfile:
			self.mapping = json.loads(mapfile.read())
		try:
			self.es = elasticsearch.Elasticsearch(elasticURL, timeout=5, max_retries=1)
			self.status = self._ping()
			if self.status:
				self._initialize_indices()
		except Exception:
			self.status = False
			raise
		finally:
			# Set the lastReconnectAttempt to the timestamp after initialization
			self.lastReconnectAttempt = datetime.utcnow()
		return

	def _initialize_indices(self):
		''' Check each required index and make sure it exists, if it doesn't then create it '''
		for index in self.natlasIndices:
			if not self.es.indices.exists(index):
				self.es.indices.create(index, body=self.mapping)

	def _ping(self):
		''' Returns True if the cluster is up, False otherwise'''
		return self.es.ping()

	def _attempt_reconnect(self):
		''' Attempt to reconnect if we haven't tried to reconnect too recently '''
		now = datetime.utcnow()
		delta = now - self.lastReconnectAttempt
		if delta.seconds < 30:
			return self.status
		else:
			self.status = self._ping()
			return self.status

	def _check_status(self):
		''' If we're in a known bad state, try to reconnect '''
		if not self.status and not self._attempt_reconnect():
			raise elasticsearch.ConnectionError
		return self.status

	def _execute_raw_query(self, func, **kargs):
		''' Wraps the es client to make sure that ConnectionErrors are handled uniformly '''
		self._check_status()
		try:
			results = func(**kargs)
			return results
		except elasticsearch.ConnectionError:
			self.status = False
			raise elasticsearch.ConnectionError

	def execute_search(self, **kargs):
		''' Execute an arbitrary search. This is where we should instrument things specific to es.search '''
		results = self._execute_raw_query(self.es.search, doc_type='_doc', **kargs)
		return results

	def execute_count(self, **kargs):
		''' Executes an arbitrary count. This is where we should instrument things specific to es.count '''
		results = self._execute_raw_query(self.es.count, doc_type='_doc', **kargs)
		if not results:
			return 0
		return results

	def execute_delete_by_query(self, **kargs):
		''' Executes an arbitrary delete_by_query. This is where we should instrument things specific to es.delete_by_query '''
		results = self._execute_raw_query(self.es.delete_by_query, doc_type='_doc', **kargs)
		return results

	def execute_index(self, **kargs):
		''' Executes an arbitrary index. This is where we should instrument things specific to es.index '''
		results = self._execute_raw_query(self.es.index, doc_type='_doc', **kargs)
		return results

	def get_collection(self, **kargs):
		''' Execute a search and return a collection of results '''
		results = self.execute_search(**kargs)
		if not results:
			return 0, []
		docsources = self.collate_source(results['hits']['hits'])
		return results['hits']['total'], docsources

	def get_single_host(self, **kargs):
		''' Execute a search and return a single result '''
		results = self.execute_search(**kargs)
		if not results or results['hits']['total'] == 0:
			return 0, None
		return results['hits']['total'], results['hits']['hits'][0]['_source']

	def collate_source(self, documents):
		return map(lambda doc: doc['_source'], documents)
