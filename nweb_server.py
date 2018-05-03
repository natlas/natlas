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
  query = request.args.get('q', '')
  page = int(request.args.get('p', 0))
  format = request.args.get('f', "")

  count,context = nweb.search(q,100,100*int(str(p)))

  # what kind of output are we looking for?
  if format == 'hostlist':
    return render_template("hostlist.html",query=query, numresults=count, page=page, hosts=context)

  # default output (a pretty webpage)
  return render_template("search.html",query=query, numresults=count, page=page, hosts=context)

@app.route('/getwork')
def getwork():

  try:
    return nweb.getwork_mass()
  except:
    print("masscan data not loaded, falling back to the old way")

  random.seed(os.urandom(200))
  scope=[]
  try:
    for line in open("config/scope.txt"):
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
    for line in open("config/blacklist.txt"):
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
    return "[!] Couldn't find necessary nmap_data\n"

  if len(newhost['ports']) == 2:
    return "no open ports!"

  if len(newhost['ports']) > 500:
    return "[!] More than 500 ports found. This is probably an IDS/IPS. We're going to throw the data out."

  nweb.newhost(newhost)

  return "ip: "+newhost['ip']+"\nhostname: "+newhost['hostname']+"\nports: "+newhost['ports']

