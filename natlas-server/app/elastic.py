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
                        myIndexInit = {"mappings":{"_doc":{"properties":{
                            "ctime": {"type":"date"},
                            "agent": {"type":"keyword"},
                            "agent_version": {"type":"keyword"},
                            "scan_reason": {"type":"keyword"},
                            "scan_start": {"type":"date"},
                            "scan_stop": {"type":"date"},
                            "elapsed": {"type":"integer"},
                            "tags": {"type":"keyword"},
                            "port_count": {"type":"integer"},
                            "port_str": {"type":"text"},
                            "is_up": {"type":"boolean"},
                            "ip": {"type":"ip"},
                            "scan_id": {"type":"keyword"},
                            "nmap_data": {"type": "text"},
                            "xml_data": {"type": "text", "index":"false"},
                            "gnmap_data": {"type": "text", "index": "false"},
                            "httpsheadshot": {"type": "binary"},
                            "httpsheadshot": {"type": "binary"},
                            "vncheadshot": {"type":"binary"},
                            "ports": {"type": "nested", "properties": {
                                "id" : {"type": "keyword"},
                                "number" : {"type": "integer"},
                                "protocol": {"type": "keyword"},
                                "state": {"type": "keyword"},
                                "reason": {"type": "text"},
                                "banner": {"type": "text"},
                                "service": {
                                   "properties": {
                                       "name": {"type": "keyword"},
                                       "product": {"type": "keyword"},
                                       "version": {"type": "keyword"},
                                       "ostype": {"type": "keyword"},
                                       "conf": {"type": "integer"},
                                       "cpelist": {"type": "text"},
                                       "method": {"type": "text"},
                                       "extrainfo": {"type": "text"},
                                       "tunnel": {"type": "keyword"}
                                     }
                                   },
                                   "scripts": {
                                        "properties": {
                                            "id": {"type": "text"},
                                            "output": {"type": "text"}
                                        }
                                   }

                            }}
                            }}}}
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
        except:
            return 0, []  # search borked, return nothing

        results = []  # collate results
        for thing in result['hits']['hits']:
            results.append(thing['_source'])

        return result['hits']['total'], results

    def totalHosts(self):
        result = self.es.count(index="nmap", doc_type="_doc")
        return result["count"]

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


    def delete_scan(self, scan_id):
        if not self.status:
            return -1

        migrate = False
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

    def delete_host(self, ip):
        if not self.status:
            return -1

        deleted = self.es.delete_by_query(index="nmap,nmap_history", doc_type="_doc", body={"query": {
                                "query_string": {'query': ip, "fields": ["ip", "id"], "default_operator": "AND"}}, "sort": {"ctime": {"order": "desc"}}})
        return deleted["deleted"]
