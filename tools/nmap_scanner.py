#!/usr/bin/python3

'''
Submits nmap scans to natlas from local targets.txt.
'''
import sys
import requests
import subprocess
import time
import os
import random
import string
import json
import base64

import threading
import multiprocessing
import multiprocessing.pool
from netaddr import *

scope = []

try:
  import ipaddress
except:
  print("you should be using python3!")
  sys.exit()

def scan(target):

  server="http://127.0.0.1:5000"
  print("target is "+target)

  # scan server
  rand = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
  print("random value is "+rand)
  process = subprocess.Popen(["nmap","-oA","data/natlas."+rand,"-A","-open",target],stdout=subprocess.PIPE)
  try:
    out, err = process.communicate(timeout=360) # 6 minutes
  except:
    try:
      print("killing slacker process")
      process.kill()
    except:
      print("okay, seems like it was already dead")

  print("scan complete, nice")

  result={}
  for ext in 'nmap','gnmap','xml':
    result[ext+"_data"]=open("data/natlas."+rand+"."+ext).read()
    os.remove("data/natlas."+rand+"."+ext)
    print("sending and deleting natlas."+rand+"."+ext)

  if len(result['nmap_data']) < 250:
    print("this data looks crappy")
    return
  else:
    print("size was "+str(len(result['nmap_data'])))

  # submit result
  response=requests.post(server+"/submit",json=json.dumps(result)).text
  print("response is:\n"+response)

if len(sys.argv) != 2:
    print("./nmap-scanner.py <targets.txt>")
    sys.exit(1)

for target in open(sys.argv[1], "r"):
    scope.append(IPNetwork(target))

max_threads=3

for network in scope:
  for ip in network:
    if threading.active_count() < max_threads:
      notifylock=False
      print("number of threads : "+str(threading.active_count()))
      t = threading.Thread(target=scan(str(ip)))
      t.start()
    else:
      if notifylock is False:
        print("too many threads .. waiting")
      notifylock=True

    time.sleep(1)
