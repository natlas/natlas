import sys
import urllib2
import subprocess
import time

import threading
import multiprocessing
import multiprocessing.pool

def scan():
  # pull target
  server="http://127.0.0.1:8000"
  #server="https://nweb.io"
  target = urllib2.urlopen(server+"/getwork").read()
  print("target is "+target)

  # scan server 
  process = subprocess.Popen(["nmap","-A","-open",target],stdout=subprocess.PIPE)
  out, err = process.communicate()
  print("scan complete, nice")
  #print(out)

  # submit result
  response=urllib2.urlopen(server+"/submit",data=out).read()
  print("response is:\n"+response)

max_threads=30

while True:
  if threading.active_count() < max_threads:
    notifylock=False
    print "number of threads : "+str(threading.active_count())
    t = threading.Thread(target=scan)
    t.start()
    time.sleep(1)
  else:
    if notifylock is False:
      print "too many threads .. waiting"
    notifylock=True
  
  time.sleep(1)


