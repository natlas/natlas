import json
import elasticsearch
import sys
from datetime import datetime
from config import Config
import logging


class Elastic:
	es = None
	status = False
	errrorinfo = ''
	natlasIndices = ["nmap", "nmap_history"]
	mapping = {}
	lastReconnectAttempt = datetime.utcnow()
	logger = logging.getLogger('elasticsearch')
	logger.setLevel('ERROR')

	def __init__(self, elasticURL):
		with open(Config().BASEDIR + '/defaults/elastic/mapping.json') as mapfile:
			self.mapping = json.loads(mapfile.read())
		try:
			self.es = elasticsearch.Elasticsearch(elasticURL, timeout=5, max_retries=1)
			self.status = self.ping()
			if self.status:
				self.initialize_indices()
		except Exception as e:
			self.errorinfo = e
			self.status = False
			return

	def initialize_indices(self):
		''' Check each required index and make sure it exists, if it doesn't then create it '''
		for index in self.natlasIndicies:
			if not self.es.indices.exists(index):
				self.es.indices.create(index, body=self.mapping)

	def ping(self):
		''' Returns True if the cluster is up, False otherwise'''
		return self.es.ping()

	def attempt_reconnect(self):
		now = datetime.utcnow()
		delta = now - self.lastReconnectAttempt
		if delta.seconds < 5:
			return self.status
		else:
			self.status = self.ping()
			return self.status

	def check_status(self):
		if not self.status:
			if not self.attempt_reconnect():
				raise elasticsearch.ConnectionError
		return self.status

	def execute_raw_query(self, func, **kargs):
		self.check_status()
		try:
			results = func(**kargs)
			return results
		except elasticsearch.ConnectionError:
			self.status = False
			raise elasticsearch.ConnectionError
		except Exception:
			return None

	def execute_search(self, **kargs):
		''' Execute an arbitrary search. This is where we should instrument things specific to es.search '''
		results = self.execute_raw_query(self.es.search, doc_type='_doc', **kargs)
		return results

	def get_collection(self, **kargs):
		''' Execute a search and return a collection of results '''
		results = self.execute_search(**kargs)
		if not results:
			return 0, []
		docsources = []
		for result in results['hits']['hits']:
			docsources.append(result['_source'])
		return results['hits']['total'], docsources

	def get_single_host(self, **kargs):
		''' Execute a search and return a single result '''
		results = self.execute_search(**kargs)
		if not results or results['hits']['total'] == 0:
			return 0, None
		return results['hits']['total'], results['hits']['hits'][0]['_source']

	def execute_count(self, **kargs):
		''' Executes an arbitrary count. This is where we should instrument things specific to es.count '''
		results = self.execute_raw_query(self.es.count, doc_type='_doc', **kargs)
		if not results:
			return 0
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
		result = self.get_collection(index=searchIndex, body=searchBody)
		return result

	def total_hosts(self):
		''' Count the number of documents in nmap and return the count '''
		result = self.execute_count(index="nmap")
		return result["count"]

	def newhost(self, host):
		self.checkStatus()
		ip = str(host['ip'])

		try:
			self.es.index(index='nmap_history', doc_type='_doc', body=host)
			self.es.index(index='nmap', doc_type='_doc', id=ip, body=host)
			return True
		except elasticsearch.ElasticsearchException:
			self.status = False
			raise elasticsearch.ConnectionError

	def gethost(self, ip):
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
		result = self.get_single_host(index='nmap_history', body=searchBody)
		return result


	def gethost_history(self, ip, limit, offset):
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
		result = self.get_collection(index='nmap_history', body=searchBody)
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
		result = self.execute_search(index="nmap_history", body=searchBody, size=0, _source=False, track_scores=False)
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
		result = self.get_collection(index="nmap_history", body=searchBody, _source=source_fields, track_scores=False)
		return result

	def gethost_scan_id(self, scan_id):
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
		result = self.get_single_host(index='nmap_history', body=searchBody)
		return result

	def delete_scan(self, scan_id):
		self.check_status()

		migrate = False
		try:
			searchBody = {
				"size": 1,
				"query": {
					"query_string": {
						"query": scan_id,
						"fields": ["scan_id"]
					}
				}
			}
			hostResult = self.es.search(index='nmap', doc_type='_doc', body=searchBody)
			if hostResult['hits']['total'] != 0:
				# we're deleting the most recent scan result and need to pull the next most recent into the nmap index
				# otherwise you won't find the host when doing searches or browsing
				ipaddr = hostResult['hits']['hits'][0]['_source']['ip']
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
				twoscans = self.es.search(index="nmap_history", doc_type="_doc", body=secondBody)

				if len(twoscans['hits']['hits']) != 2:
					# we're deleting the only scan for this host so we don't need to migrate old scan data into the nmap index
					migrate = False
				else:
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
			result = self.es.delete_by_query(index="nmap,nmap_history", doc_type="_doc", body=deleteBody)
			if migrate:
				self.es.index(index='nmap', doc_type='_doc', id=ipaddr, body=twoscans['hits']['hits'][1]['_source'])
			return result["deleted"]
		except elasticsearch.ConnectionError:
			self.status = False
			raise elasticsearch.ConnectionError

	def delete_host(self, ip):
		self.check_status()
		try:
			searchBody = {
				"query": {
					"query_string": {
						"query": ip,
						"fields": ["ip", "id"],
						"default_operator": "AND"
					}
				},
				"sort": {
					"ctime": {
						"order": "desc"
					}
				}
			}
			deleted = self.es.delete_by_query(index="nmap,nmap_history", doc_type="_doc", body=searchBody)
			return deleted["deleted"]
		except elasticsearch.ConnectionError:
			self.status = False
			raise elasticsearch.ConnectionError

	def random_host(self):
		self.check_status()
		import random
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
		try:

			random = self.es.search(index="nmap", doc_type="_doc", body=searchBody)
			return random
		except elasticsearch.ConnectionError:
			self.status = False
			raise elasticsearch.ConnectionError

	def get_current_screenshots(self, limit, offset):
		self.check_status()
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
		try:
			result = self.es.search(index="nmap", doc_type='_doc', body=searchBody, _source=source_fields, track_scores=False)
			num_screenshots = int(result['aggregations']["screenshot_count"]["value"])
			results = []  # collate results
			for thing in result['hits']['hits']:
				results.append(thing['_source'])

			return result['hits']['total'], num_screenshots, results
		except elasticsearch.ConnectionError:
			self.status = False
			raise elasticsearch.ConnectionError
