import json
from elasticsearch import Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

def search(query,limit,offset):

    if query=='':
        query='nmap'

    print("query is %s",query)

    try:
      result = es.search(index="nweb", doc_type="nmap", body={"size":limit, "from":offset, "query": {"query_string": { 'query':query, "fields":["nmap_data"], "default_operator":"AND"  } },"sort": { "ctime": { "order": "desc" }}})
    except:
      return 0,[] # search borked, return nothing

    #result = es.search(index="nweb", doc_type="nmap", body={"size":limit, "from":offset, "query": {"match": {'nmap_data':query}}})
    count = 1

    results=[] # collate results
    for thing in result['hits']['hits']:
        results.append(thing['_source'])

    return result['hits']['total'],results

def newhost(host):
    ip = str(host['ip'])
    # broken in ES6
    #es.index(index='nweb', doc_type='nmap_history', body=host)
    es.index(index='nweb', doc_type='nmap', id=ip, body=host)

def gethost(ip):
    result = es.get(index='nweb', doc_type='nmap', id=ip)
    return result['_source']
