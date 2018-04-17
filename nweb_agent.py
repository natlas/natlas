#!/usr/bin/python3

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

# my script for headshotting servers
from getheadshot import getheadshot

try:
  import ipaddress
except:
  print("you should be using python3!")
  sys.exit()

def scan():
  # pull target
  server="http://127.0.0.1:5000"
  #server="https://nweb.io"
  target_data = json.loads(requests.get(server+"/getwork").text)
  target = target_data["target"]
  print("target is "+target)

  #if ipaddress.ip_address(target).is_private:
  #  print("no I'm not going to scan a private ip.. "+target)
  #  return

  # scan server 
  rand = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
  print("random value is "+rand)

  command = ["nmap","-oA","data/nweb."+rand,"-A","-open",target]

  if 'ports' in target_data:
    command.append('-p')
    command.append(str(target_data['ports'])[1:-1])

  process = subprocess.Popen(command,stdout=subprocess.PIPE)
  try:
    out, err = process.communicate(timeout=360) # 6 minutes
  except:
    try:
      print("killing slacker process")
      process.kill()
    except:
      print("okay, seems like it was already dead")

  print("scan complete, nice")
  #print(out)

  result={}
  for ext in 'nmap','gnmap','xml':
    result[ext+"_data"]=open("data/nweb."+rand+"."+ext).read()
    os.remove("data/nweb."+rand+"."+ext)
    print("sending and deleting nweb."+rand+"."+ext)

  if len(result['nmap_data']) < 250:
    print("this data looks crappy")
    return
  else:
    print("size was "+str(len(result['nmap_data'])))

  if getheadshot(target,rand) is True:
    result['headshot']=str(base64.b64encode(open("data/nweb."+rand+".headshot.jpg",'rb').read()))[2:-1]
    os.remove("data/nweb."+rand+".headshot.jpg")
    print("submitting headshot")

  # submit result
  response=requests.post(server+"/submit",json=json.dumps(result)).text
  print("response is:\n"+response)

max_threads=3

# uncomment these to test (run single scan)
#scan()
#exit()

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
