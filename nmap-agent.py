#!/usr/bin/python3

import sys
import requests
import subprocess
import time
import os
import random
import string
import json

import threading
import multiprocessing
import multiprocessing.pool

try:
  import ipaddress
except:
  print("you should be using python3!")
  sys.exit()

def scan():
  # pull target
  server="http://127.0.0.1:5000"
  #server="https://nweb.io"
  target = requests.get(server+"/getwork").text
  print("target is "+target)

  #if ipaddress.ip_address(target).is_private:
  #  print("no I'm not going to scan a private ip.. "+target)
  #  return

  # scan server 
  rand = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
  print("random value is "+rand)
  process = subprocess.Popen(["nmap","-oA","nweb."+rand,"-A","-open",target],stdout=subprocess.PIPE)
  out, err = process.communicate()
  print("scan complete, nice")
  #print(out)

  result={}
  for ext in 'nmap','gnmap','xml':
    result[ext+"_data"]=open("nweb."+rand+"."+ext).readlines()
    os.remove("nweb."+rand+"."+ext)
    print("sending and deleting nweb."+rand+"."+ext)

  # submit result
  response=requests.post(server+"/submit",data=json.dumps(result)).text
  print("response is:\n"+response)

max_threads=10

scan()
exit()

while True:
  if threading.active_count() < max_threads:
    notifylock=False
    print("number of threads : "+str(threading.active_count()))
    t = threading.Thread(target=scan)
    t.start()
  else:
    if notifylock is False:
      print("too many threads .. waiting")
    notifylock=True

  time.sleep(1)
