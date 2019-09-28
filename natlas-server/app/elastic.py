import json
import elasticsearch
import random
from datetime import datetime
from config import Config
from urllib3.exceptions import NewConnectionError

class Elastic:
	es = None
	status = False
	errrorinfo = ''
	natlasIndices = ["nmap", "nmap_history"]
	mapping = {}
	lastReconnectAttempt = None

	def __init__(self, elasticURL):
		with open(Config().BASEDIR + '/defaults/elastic/mapping.json') as mapfile:
			self.mapping = json.loads(mapfile.read())
		try:
			self.es = elasticsearch.Elasticsearch(elasticURL, timeout=5, max_retries=1)
			if "cluster_name" in self.es.nodes.info():
				self.status = True
			if self.status:
				for index in self.natlasIndices: # initialize nmap and nmap_history and give them mappings for known necessary types
					if not self.es.indices.exists(index):
						self.es.indices.create(index, body=self.mapping)
		except NewConnectionError:
			self.errorinfo = 'urllib3.exceptions.NewConnectionError'
			return
		except ConnectionRefusedError:
			self.errorinfo = 'ConnectionRefusedError'
			return
		except elasticsearch.exceptions.NotFoundError:
			self.errorinfo = 'Cluster Not Found'
			return
		except:
			self.lastReconnectAttempt = datetime.now()
			self.errorinfo = 'Could not establish connection'
			return

	def attemptReconnect(self):
		now = datetime.now()
		delta = now - self.lastReconnectAttempt
		if delta.seconds < 60:
			return False
		else:
			try:
				if "cluster_name" in self.es.nodes.info():
					self.status = True
					return True
				else:
					self.lastReconnectAttempt = now
					return False
			except:
				self.lastReconnectAttempt = now
				return False

	def search(self, query, limit, offset):
		if not self.status:
			if not self.attemptReconnect():
				return 0,[]
		if query == '':
			query = 'nmap'
		try:
			result = self.es.search(index="nmap", doc_type="_doc", body=\
				{
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
				})
			results = []  # collate results
			for thing in result['hits']['hits']:
				results.append(thing['_source'])

			return result['hits']['total'], results
		except (NewConnectionError, elasticsearch.exceptions.ConnectionError):
			self.status = False
		except:
			return 0, []  # search borked, return nothing



	def totalHosts(self):
		if not self.status:
			if not self.attemptReconnect():
				return 0
		try:
			result = self.es.count(index="nmap", doc_type="_doc")
			return result["count"]
		except (NewConnectionError, elasticsearch.exceptions.ConnectionError):
			self.status = False
			return 0

	def newhost(self, host):
		if not self.status:
			if not self.attemptReconnect():
				return
		ip = str(host['ip'])

		try:
			self.es.index(index='nmap_history', doc_type='_doc', body=host)
			self.es.index(index='nmap', doc_type='_doc', id=ip, body=host)
		except (NewConnectionError, elasticsearch.exceptions.ConnectionError):
			self.status = False
			return

	def gethost(self, ip):
		if not self.status:
			if not self.attemptReconnect():
				return 0,[]
		try:
			result = self.es.search(index='nmap_history', doc_type='_doc', body={"size": 1, "query": {"query_string": {
									'query': ip, "fields": ["ip"], "default_operator": "AND"}}, "sort": {"ctime": {"order": "desc"}}})
			if result['hits']['total'] == 0:
				return 0, None
			return result['hits']['total'], result['hits']['hits'][0]['_source']
		
		except (NewConnectionError, elasticsearch.exceptions.ConnectionError):
			self.status = False
			return 0, None


	def gethost_history(self, ip, limit, offset):
		if not self.status:
			if not self.attemptReconnect():
				return 0,[]
		try:
			result = self.es.search(index='nmap_history', doc_type='_doc', body={"size": limit, "from": offset, "query": {
									"query_string": {'query': ip, "fields": ["ip"], "default_operator": "AND"}}, "sort": {"ctime": {"order": "desc"}}})
			results = []  # collate results
			for thing in result['hits']['hits']:
				results.append(thing['_source'])

			return result['hits']['total'], results
		
		except (NewConnectionError, elasticsearch.exceptions.ConnectionError):
			self.status = False
			return 0, None

	def gethost_scan_id(self, scan_id):
		if not self.status:
			if not self.attemptReconnect():
				return 0,[]

		try:
			result = self.es.search(index='nmap_history', doc_type='_doc', body={"size": 1, "query": {
									"query_string": {'query': scan_id, "fields": ["scan_id"], "default_operator": "AND"}}, "sort": {"ctime": {"order": "desc"}}})
			if result['hits']['total'] == 0:
				return 0, None
			return result['hits']['total'], result['hits']['hits'][0]['_source']

		except (NewConnectionError, elasticsearch.exceptions.ConnectionError):
			self.status = False
			return 0, None



	def delete_scan(self, scan_id):
		if not self.status:
			if not self.attemptReconnect():
				return -1

		migrate = False
		try:
			hostResult = self.es.search(index='nmap', doc_type='_doc', body={"size": 1, "query": {
									"query_string": {'query': scan_id, "fields": ["scan_id"]}}})
			if hostResult['hits']['total'] != 0:
				# we're deleting the most recent scan result and need to pull the next most recent into the nmap index
				# otherwise you won't find the host when doing searches or browsing
				ipaddr = hostResult['hits']['hits'][0]['_source']['ip']
				twoscans = self.es.search(index="nmap_history", doc_type="_doc", body={"size":2, "query": {
							   "query_string": {"query": ipaddr, "fields": ["ip"]}}, "sort": {"ctime": {"order": "desc"}}})

				if len(twoscans['hits']['hits']) != 2:
					# we're deleting the only scan for this host so we don't need to migrate old scan data into the nmap index
					migrate = False
				else:
					migrate = True
			result = self.es.delete_by_query(index="nmap,nmap_history", doc_type="_doc", body={"query": {
									 "query_string": {"query": scan_id, "fields": ["scan_id"], "default_operator": "AND"}}})
			if migrate:
				self.es.index(index='nmap', doc_type='_doc', id=ipaddr, body=twoscans['hits']['hits'][1]['_source'])
			return result["deleted"]
		except (NewConnectionError, elasticsearch.exceptions.ConnectionError):
			self.status = False
			return False

	def delete_host(self, ip):
		if not self.status:
			if not self.attemptReconnect():
				return -1
		try:
			deleted = self.es.delete_by_query(index="nmap,nmap_history", doc_type="_doc", body={"query": {
									"query_string": {'query': ip, "fields": ["ip", "id"], "default_operator": "AND"}}, "sort": {"ctime": {"order": "desc"}}})
			return deleted["deleted"]
		except (NewConnectionError, elasticsearch.exceptions.ConnectionError):
			self.status = False
			return False
