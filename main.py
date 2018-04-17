import flask
from flask import render_template
from flask import request
from flask import Flask
from flask import g
app = Flask(__name__,static_url_path='/static')

from netaddr import *
import time
import os
import json
import random
import sys
import traceback
import sqlite3

import models_elastic as nweb
from nmap_helper import * # get_ip etc

from datetime import datetime

# Create your views here.
@app.route('/host')
def host():
  h = request.args.get('h')
  context = nweb.gethost(h)
  return render_template("host.html",**context)

@app.route('/')
def search():
  q = request.args.get('q')
  if not q:
    q=''
  f = request.args.get('f')
  try:
    p = int(request.args.get('p'))
  except:
    p = 0

  try:
    fmt=request.args.get('f')
    print(fmt)
  except:
    fmt=""

  count,context = nweb.search(q,100,100*int(str(p)))

  # what kind of output are we looking for?
  if fmt == 'hostlist':
    print("printing hostlist because "+fmt)
    return render_template("hostlist.html",query=q, numresults=count, page=p, hosts=context)

  # default output (a pretty webpage)
  return render_template("search2.html",query=q, numresults=count, page=p, hosts=context)

@app.route('/getwork')
def getwork():
  print("getting work")

  try:
    return nweb.getwork_mass()
  except:
    print("masscan data not loaded, falling back to the old way")

  random.seed(os.urandom(200))
  scope=[]
  try:
    for line in open("scope.txt"):
      try:
        scope.append(IPNetwork(line))
      except:
        print("line "+str(line)+" in scope.txt failed to parse")
  except:
    print("failed to find scope.txt")
    scope=[]
    scope.append(IPNetwork("127.0.0.1"))

  blacklist=[]
  try:
    for line in open("blacklist.txt"):
      blacklist.append(IPNetwork(line))
  except Exception as e:
    print("failed to parse blacklist.txt "+str(e)[:-1]+" '"+line[:-1]+"'")
    blacklist=[]

  # how many hosts are in scope?
  magnitude = sum(len(network) for network in scope)

  attempts=0
  work = {}
  work['type']='nmap'
  while attempts<1000:
    # pick one
    index = random.randint(0,magnitude-1);
    attempts = attempts+1

    target=""
    for network in scope:
      if index>=len(network):
        index-=len(network)
      else:
        #target=network[index]
        isgood=True
        for badnet in blacklist: # run through the blacklist looking for match
          if network[index] in badnet:
            #print("the ip is in the blacklist! "+str(network[index]))
            isgood=False
        if isgood:
          #print("the ip is not in the blacklist! "+str(network[index]))
          work['target']=str(network[index])
          return json.dumps(work)
  return "none"

@app.route('/submit',methods=['POST'])
def submit():

  data = request.get_json()
  #data = data.replace('\\n','\n') # this is stupid

  newhost={}
  newhost=json.loads(data)

  try:
    newhost['ip'] = get_ip(newhost['nmap_data'])
    newhost['hostname'] = get_hostname(newhost['nmap_data'])
    newhost['ports'] = str(get_ports(newhost['nmap_data']))
    newhost['ctime'] = datetime.now()
    #country = get_country(ip)
  except Exception as e:
    return "you fucked it up!\n"+str(traceback.format_exc())

  if len(newhost['ports']) == 2:
    return "no open ports!"

  if len(newhost['ports']) > 500:
    return "something's fuckey.."

  nweb.newhost(newhost)

  return "ip: "+newhost['ip']+"\nhostname: "+newhost['hostname']+"\nports: "+newhost['ports']

