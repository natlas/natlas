import json
import elasticsearch
import random


class Elastic:
    es = None
    status = False
    errrorinfo = ''
    natlasIndices = ["nmap", "nmap_history"]

    def __init__(self, elasticURL):
        try:
            self.es = elasticsearch.Elasticsearch(elasticURL, timeout=5, max_retries=1)
            if "cluster_name" in self.es.nodes.info():
                self.status = True
            if self.status:
                for index in self.natlasIndices: # initialize nmap and nmap_history and give them mappings for known necessary types
                    if not self.es.indices.exists(index):
                        myIndexInit = {"mappings":{"_doc":{"properties":{"ctime":{"type":"date"}, "ip":{"type":"ip"}, "scan_id":{"type":"keyword"}}}}}
                        self.es.indices.create(index, body=myIndexInit)
        except elasticsearch.exceptions.NotFoundError:
            self.errorinfo = 'Cluster Not Found'
        except:
            self.errorinfo = 'Could not establish connection'


    def search(self, query, limit, offset):
        if not self.status:
            return 0,[]
        if query == '':
            query = 'nmap'

        try:
            result = self.es.search(index="nmap", doc_type="_doc", body={"size": limit, "from": offset, "query": {"query_string": {
                                    'query': query, "fields": ["nmap_data"], "default_operator": "AND"}}, "sort": {"ctime": {"order": "desc"}}})
        except:
            return 0, []  # search borked, return nothing

        results = []  # collate results
        for thing in result['hits']['hits']:
            results.append(thing['_source'])

        return result['hits']['total'], results

    def newhost(self, host):
        if not self.status:
            return
        ip = str(host['ip'])
        # broken in ES6
        self.es.index(index='nmap_history', doc_type='_doc', body=host)
        self.es.index(index='nmap', doc_type='_doc', id=ip, body=host)

    def gethost(self, ip):
        if not self.status:
            return 0,[]
        result = self.es.search(index='nmap_history', doc_type='_doc', body={"size": 1, "query": {"query_string": {
                                'query': ip, "fields": ["ip"], "default_operator": "AND"}}, "sort": {"ctime": {"order": "desc"}}})
        if result['hits']['total'] == 0:
            return 0, None
        return result['hits']['total'], result['hits']['hits'][0]['_source']

    def gethost_history(self, ip, limit, offset):
        if not self.status:
            return 0,[]
        result = self.es.search(index='nmap_history', doc_type='_doc', body={"size": limit, "from": offset, "query": {
                                "query_string": {'query': ip, "fields": ["ip"], "default_operator": "AND"}}, "sort": {"ctime": {"order": "desc"}}})

        results = []  # collate results
        for thing in result['hits']['hits']:
            results.append(thing['_source'])

        return result['hits']['total'], results

    def gethost_scan_id(self, scan_id):
        if not self.status:
            return 0,[]
        result = self.es.search(index='nmap_history', doc_type='_doc', body={"size": 1, "query": {
                                "query_string": {'query': scan_id, "fields": ["scan_id"], "default_operator": "AND"}}, "sort": {"ctime": {"order": "desc"}}})

        if result['hits']['total'] == 0:
            return 0, None
        return result['hits']['total'], result['hits']['hits'][0]['_source']