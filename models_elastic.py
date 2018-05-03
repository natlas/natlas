import json
from elasticsearch import Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
import random

def search(query,limit,offset):

  if query=='':
    query='nmap'

  try:
    result = es.search(index="nmap", doc_type="_doc", body={"size":limit, "from":offset, "query": {"query_string": { 'query':query, "fields":["nmap_data"], "default_operator":"AND"  } },"sort": { "ctime": { "order": "desc" }}})
  except:
    return 0,[] # search borked, return nothing

  #result = es.search(index="nmap", doc_type="_doc", body={"size":limit, "from":offset, "query": {"match": {'nmap_data':query}}})
  count = 1

  results=[] # collate results
  for thing in result['hits']['hits']:
    results.append(thing['_source'])

  return result['hits']['total'],results

def newhost(host):
  ip = str(host['ip'])
  # broken in ES6
  es.index(index='nmap_history', doc_type='_doc', body=host)
  es.index(index='nmap', doc_type='_doc', id=ip, body=host)

def gethost(ip):
  result = es.get(index='nmap', doc_type='_doc', id=ip)
  return result['_source']

def getwork_mass(): # getwork when masscan data is loaded

  # get random ip
  result = es.search(index="masscan_hosts", doc_type="_doc", body={"size": 1,"query": {"function_score": {"functions": [{"random_score": {"seed": random.randint(0,2**60)}}]}}})
  randip = str(result['hits']['hits'][0]['_source']['ip'])

  # get ports
  result = es.search(index="masscan_services", doc_type="_doc", body={"size": 1000,"query": {"match": {'ip':randip}}})
  ports=[] # collate results
  for thing in result['hits']['hits']:
    ports.append(thing['_source']['ports'][0]['port'])

  work = {}
  work['type']='nmap'
  work['target']=randip
  work['ports']=ports
  return json.dumps(work)

