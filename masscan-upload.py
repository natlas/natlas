import json
from elasticsearch import Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

f=open("masscan.json")

for line in f:
  print("inserting "+json.loads(line[:-2])['ip'])
  # ip is unique for "hosts", and "services" indexes all ports
  es.index(index='masscan_hosts', doc_type="_doc", id=json.loads(line[:-2])['ip'],body=line[:-2])
  es.index(index='masscan_services', doc_type="_doc", body=line[:-2])

