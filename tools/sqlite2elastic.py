import json
import requests
import sqlite3
conn = sqlite3.connect('nweb.db')
c = conn.cursor()

c.execute('select hostname,nmap_data,gnmap_data,xml_data from sightings')

rows = c.fetchall()

for row in rows:
  print(row[0])
  result={}
  result['nmap_data']=row[1]
  result['gnmap_data']=row[2]
  result['xml_data']=row[3]
  requests.post("http://127.0.0.1:5000/submit",json=json.dumps(result)).text

