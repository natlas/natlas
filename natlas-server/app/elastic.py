import json
import elasticsearch
import sys
from datetime import datetime
from config import Config
import logging
import random


class Elastic:
	es = None
	status = False
	natlasIndices = ["nmap", "nmap_history"]
	mapping = {}
	lastReconnectAttempt = None
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
			return
		finally:
			# Set the lastReconnectAttempt to the timestamp after initialization
			self.lastReconnectAttempt = datetime.utcnow()

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
		except Exception:
			return None

	def _execute_search(self, **kargs):
		''' Execute an arbitrary search. This is where we should instrument things specific to es.search '''
		results = self._execute_raw_query(self.es.search, doc_type='_doc', **kargs)
		return results

	def _execute_count(self, **kargs):
		''' Executes an arbitrary count. This is where we should instrument things specific to es.count '''
		results = self._execute_raw_query(self.es.count, doc_type='_doc', **kargs)
		if not results:
			return 0
		return results

	def _execute_delete_by_query(self, **kargs):
		''' Executes an arbitrary delete_by_query. This is where we should instrument things specific to es.delete_by_query '''
		results = self._execute_raw_query(self.es.delete_by_query, doc_type='_doc', **kargs)
		return results

	def _execute_index(self, **kargs):
		''' Executes an arbitrary index. This is where we should instrument things specific to es.index '''
		results = self._execute_raw_query(self.es.index, doc_type='_doc', **kargs)
		return results

	def _get_collection(self, **kargs):
		''' Execute a search and return a collection of results '''
		results = self._execute_search(**kargs)
		if not results:
			return 0, []
		docsources = self._collate_source(results['hits']['hits'])
		return results['hits']['total'], docsources

	def _get_single_host(self, **kargs):
		''' Execute a search and return a single result '''
		results = self._execute_search(**kargs)
		if not results or results['hits']['total'] == 0:
			return 0, None
		return results['hits']['total'], results['hits']['hits'][0]['_source']

	def _collate_source(self, documents):
		results = []
		for doc in documents:
			results.append(doc['_source'])
		return results

	def search(self, limit, offset, query='nmap', searchIndex="nmap"):
		''' Execute a user supplied search and return the results '''
		searchBody = {
			"size": limit,
			"from": offset,
			"query": {
				"bool": {
					"must": [
						{
							"query_string": {
								"query": query,
								"fields": ["nmap_data"],
								"default_operator": "AND"
							}
						},
						{
							"term": {
								"is_up": True
							}
						},
						{
							"range": {
								"port_count": {
									"gt": 0
								}
							}
						}
					]
				}
			},
			"sort": {
				"ctime": {
					"order": "desc"
				}
			}
		}
		result = self._get_collection(index=searchIndex, body=searchBody)
		return result

	def total_hosts(self):
		''' Count the number of documents in nmap and return the count '''
		result = self._execute_count(index="nmap")
		return result["count"]

	def new_result(self, host):
		''' Create new elastic documents in both indices for a new scan result '''
		ip = str(host['ip'])

		self._execute_index(index='nmap_history', body=host)
		self._execute_index(index='nmap', id=ip, body=host)
		return True

	def get_host(self, ip):
		''' Gets the most recent result for a host, but by querying the nmap_history it also gives us the total number of historical results '''
		searchBody = {
			"size": 1,
			"query": {
				"query_string": {
					"query": ip,
					"fields": ["ip"],
					"default_operator":
					"AND"
				}
			},
			"sort": {
				"ctime": {
					"order": "desc"
				}
			}
		}
		result = self._get_single_host(index='nmap_history', body=searchBody)
		return result

	def get_host_history(self, ip, limit, offset):
		''' Gets a collection of historical results for a specific ip address '''
		searchBody = {
			"size": limit,
			"from": offset,
			"query": {
				"query_string": {
					"query": ip,
					"fields": ["ip"],
					"default_operator": "AND"
				}
			},
			"sort": {
				"ctime": {
					"order": "desc"
				}
			}
		}
		result = self._get_collection(index='nmap_history', body=searchBody)
		return result

	def count_host_screenshots(self, ip):
		''' Search history for an ip address and returns the number of historical screenshots '''
		searchBody = {
			"query": {
				"term": {
					"ip": ip
				}},
			"aggs": {
				"screenshot_count": {
					"sum": {
						"field": "num_screenshots"
					}
				}
			}
		}
		# By setting size to 0, _source to False, and track_scores to False, we're able to optimize this query to give us only what we care about
		result = self._execute_search(index="nmap_history", body=searchBody, size=0, _source=False, track_scores=False)
		num_screenshots = int(result['aggregations']["screenshot_count"]["value"])
		return num_screenshots

	def get_host_screenshots(self, ip, limit, offset):
		''' Gets screenshots and minimal context for a given host '''
		searchBody = {
			"size": limit,
			"from": offset,
			"query": {
				"bool": {
					"must": [
						{
							"term": {
								"ip": ip
							}
						},
						{
							"range": {
								"num_screenshots": {
									"gt": 0
								}
							}
						}
					]
				}
			},
			"sort": {
				"ctime": {
					"order": "desc"
				}
			}
		}
		source_fields = ['screenshots', 'ctime', 'scan_id']
		result = self._get_collection(index="nmap_history", body=searchBody, _source=source_fields, track_scores=False)
		return result

	def get_host_by_scan_id(self, scan_id):
		''' Get a specific historical result based on scan_id, which should be unique '''
		searchBody = {
			"size": 1,
			"query": {
				"query_string": {
					"query": scan_id,
					"fields": ["scan_id"],
					"default_operator": "AND"
				}
			},
			"sort": {
				"ctime": {
					"order": "desc"
				}
			}
		}
		result = self._get_single_host(index='nmap_history', body=searchBody)
		return result

	def delete_scan(self, scan_id):
		''' Delete a specific scan, if it's the most recent then try to migrate the next oldest back into the nmap index '''
		migrate = False
		searchBody = {
			"size": 1,
			"query": {
				"query_string": {
					"query": scan_id,
					"fields": ["scan_id"]
				}
			},
			"sort": {
				"ctime": {
					"order": "desc"
				}
			}
		}
		count, host = self._get_single_host(index='nmap', body=searchBody)
		if count != 0:
			# we're deleting the most recent scan result and need to pull the next most recent into the nmap index
			# otherwise you won't find the host when doing searches or browsing
			ipaddr = host['ip']
			secondBody = {
				"size": 2,
				"query": {
					"query_string": {
						"query": ipaddr,
						"fields": ["ip"]
					}
				},
				"sort": {
					"ctime": {
						"order": "desc"
					}
				}
			}

			count, twoscans = self._get_collection(index="nmap_history", body=secondBody)
			# If count is one then there's only one result in history so we can just delete it.
			# If count is > 1 then we need to migrate the next oldest scan data
			if count > 1:
				migrate = True
		deleteBody = {
			"query": {
				"query_string": {
					"query": scan_id,
					"fields": ["scan_id"],
					"default_operator": "AND"
				}
			}
		}
		result = self._execute_delete_by_query(index="nmap,nmap_history", body=deleteBody)
		if migrate:
			self._execute_index(index='nmap', id=ipaddr, body=twoscans[1])
		return result["deleted"]

	def delete_host(self, ip):
		''' Delete all occurrences of a given ip address '''
		searchBody = {
			"query": {
				"query_string": {
					"query": ip,
					"fields": ["ip", "id"],
					"default_operator": "AND"
				}
			}
		}
		deleted = self._execute_delete_by_query(index="nmap,nmap_history", body=searchBody)
		return deleted["deleted"]

	def random_host(self):
		''' Get a random single host and return it '''
		seed = random.randrange(sys.maxsize)
		searchBody = {
			"from": 0,
			"size": 1,
			"query": {
				"function_score": {
					"query": {
						"bool": {
							"must": [
								{
									"term": {
										"is_up": True
									}
								},
								{
									"range": {
										"port_count": {
											"gt": 0
										}
									}
								}
							]
						}
					},
					"random_score": {
						"seed": seed,
						"field": "_id"
					}
				}
			}
		}
		count, host = self._get_single_host(index="nmap", body=searchBody)
		return host

	def get_current_screenshots(self, limit, offset):
		''' Get all current screenshots '''
		searchBody = {
			"size": limit,
			"from": offset,
			"query": {
				"range": {
					"num_screenshots": {
						"gt": 0
					}
				}
			},
			"aggs": {
				"screenshot_count": {
					"sum": {
						"field": "num_screenshots"
					}
				}
			},
			"sort": {
				"ctime": {
					"order": "desc"
				}
			}
		}
		source_fields = ["screenshots", "ctime", "scan_id", "ip"]
		# We need to execute_search instead of get_collection here because we also need the aggregation information
		result = self._execute_search(index="nmap", body=searchBody, _source=source_fields, track_scores=False)
		num_screenshots = int(result['aggregations']["screenshot_count"]["value"])
		results = self._collate_source(result['hits']['hits'])

		return result['hits']['total'], num_screenshots, results
