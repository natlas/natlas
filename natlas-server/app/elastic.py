import json
import elasticsearch
import sys
from datetime import datetime
from config import Config
import logging
from flask import abort


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
			self.status = self.healthCheck()
			if self.status:
				self.initializeIndices()
		except Exception as e:
			self.errorinfo = e
			self.status = False
			return

	def initializeIndices(self):
		for index in self.natlasIndicies:
			if not self.es.indices.exists(index):
				self.es.indices.create(index, body=self.mapping)

	def healthCheck(self):
		try:
			self.es.cluster.health()
		except elasticsearch.TransportError:
			return False
		return True

	def attemptReconnect(self):
		now = datetime.utcnow()
		delta = now - self.lastReconnectAttempt
		if delta.seconds < 5:
			return self.status
		else:
			self.status = self.healthCheck()
			return self.status

	def checkStatus(self):
		if not self.status:
			if not self.attemptReconnect():
				raise elasticsearch.TransportError
		return self.status

	def search(self, query, limit, offset, searchIndex="nmap"):
		self.checkStatus()

		if query == '':
			query = 'nmap'
		try:
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
			result = self.es.search(index=searchIndex, doc_type="_doc", body=searchBody)
			results = []  # collate results
			for thing in result['hits']['hits']:
				results.append(thing['_source'])

			return result['hits']['total'], results
		except elasticsearch.TransportError:
			self.status = False
			raise elasticsearch.TransportError
		except Exception:
			abort(503)  # search borked, return nothing

	def totalHosts(self):
		self.checkStatus()
		try:
			result = self.es.count(index="nmap", doc_type="_doc")
			return result["count"]
		except elasticsearch.TransportError:
			self.status = False
			raise elasticsearch.TransportError

	def newhost(self, host):
		self.checkStatus()
		ip = str(host['ip'])

		try:
			self.es.index(index='nmap_history', doc_type='_doc', body=host)
			self.es.index(index='nmap', doc_type='_doc', id=ip, body=host)
			return True
		except elasticsearch.ElasticsearchException:
			self.status = False
			raise elasticsearch.TransportError

	def gethost(self, ip):
		self.checkStatus()
		try:
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
			result = self.es.search(index='nmap_history', doc_type='_doc', body=searchBody)
			if result['hits']['total'] == 0:
				return 0, None
			return result['hits']['total'], result['hits']['hits'][0]['_source']

		except elasticsearch.ElasticsearchException:
			self.status = False
			raise elasticsearch.TransportError

	def gethost_history(self, ip, limit, offset):
		self.checkStatus()
		try:
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
			result = self.es.search(index='nmap_history', doc_type='_doc', body=searchBody)
			results = []  # collate results
			for thing in result['hits']['hits']:
				results.append(thing['_source'])

			return result['hits']['total'], results

		except elasticsearch.TransportError:
			self.status = False
			raise elasticsearch.TransportError

	def count_host_screenshots(self, ip):
		self.checkStatus()
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
		try:
			result = self.es.search(index="nmap_history", doc_type='_doc', body=searchBody, size=0, _source=False, track_scores=False,)
			num_screenshots = int(result['aggregations']["screenshot_count"]["value"])
			return num_screenshots
		except Exception:
			self.status = False
			raise elasticsearch.TransportError

	def get_host_screenshots(self, ip, limit, offset):
		self.checkStatus()
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

		try:
			result = self.es.search(index="nmap_history", doc_type='_doc', body=searchBody, _source=["screenshots", "ctime", "scan_id"], track_scores=False,)

			results = []  # collate results
			for thing in result['hits']['hits']:
				results.append(thing['_source'])

			return result['hits']['total'], results
		except elasticsearch.TransportError:
			self.status = False
			raise elasticsearch.TransportError

	def gethost_scan_id(self, scan_id):
		self.checkStatus()

		try:
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
			result = self.es.search(index='nmap_history', doc_type='_doc', body=searchBody)
			if result['hits']['total'] == 0:
				return 0, None
			return result['hits']['total'], result['hits']['hits'][0]['_source']

		except elasticsearch.TransportError:
			self.status = False
			raise elasticsearch.TransportError

	def delete_scan(self, scan_id):
		self.checkStatus()

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
		except elasticsearch.TransportError:
			self.status = False
			raise elasticsearch.TransportError

	def delete_host(self, ip):
		self.checkStatus()
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
		except elasticsearch.TransportError:
			self.status = False
			raise elasticsearch.TransportError

	def random_host(self):
		self.checkStatus()
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
		except elasticsearch.TransportError:
			self.status = False
			raise elasticsearch.TransportError

	def get_current_screenshots(self, limit, offset):
		self.checkStatus()
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
		except elasticsearch.TransportError:
			self.status = False
			raise elasticsearch.TransportError
