import sys
import urllib2
import subprocess
import time

import threading
import multiprocessing
import multiprocessing.pool

scans=0
total_threads=0

def scan():
  global scans
  global total_threads
  scans+=1

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

  scans-=1
  total_threads-=1

  #break
  #time.sleep(5)

#scan()

max_threads=30
pool = multiprocessing.pool.ThreadPool(max_threads)
#help(pool)

while True:
  if total_threads>max_threads+10:
    time.sleep(5)
    continue
  print "new thread created .."
  total_threads+=1
  pool.apply_async(scan)
  print "running scans: "+str(scans)
  print "total threads: "+str(total_threads)
  time.sleep(1)
