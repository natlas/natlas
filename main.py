#from django.shortcuts import render
#from django.http import HttpResponse
#from django.views.decorators.http import require_http_methods
#from django.views.decorators.csrf import csrf_exempt

#from scan_manager.models import Host

import flask
from flask import render_template
from flask import request
from flask import Flask
app = Flask(__name__,static_url_path='/static')

from netaddr import *
import time
import os
import json
import random
import sys
import traceback

import models as nweb
from nmap_helper import * # get_ip etc

# Create your views here.

@app.route('/host')
def host():
  h = request.args.get('h')
  context = nweb.gethost(h)
  return render_template("host.html",**context)

@app.route('/')
def search():
  q = request.args.get('q')
  f = request.args.get('f')

  try:
    print("potato")
    fmt=request.GET['f']
    print(fmt)
    return render_template("hostlist.html")
    #return render(request,"hostlist.html",context)
  except:
    print("boo")
    fmt=""

  context = nweb.search(q)
  return render_template("search2.html",query=q, numhost=len(context), hosts=context)


  #return render(request,"search.html",context)

@app.route('/getwork')
def getwork():
  print("getting work")
  random.seed(os.urandom(200))

  scope=[]
  try:
    for line in open("scope.txt"):
      scope.append(IPNetwork(line))

  except:
    print("failed to parse scope.txt")
    scope=[]
    scope.append(IPNetwork("0.0.0.0/0"))

  # how many hosts are in scope?
  magnitude = sum(len(network) for network in scope)
  
  # pick one
  index = random.randint(0,magnitude-1);

  target=""
  for network in scope:
    if index>=len(network):
      index-=len(network)
    else:
      target=network[index]
      break

  #return HttpResponse("google.com")
  return str(target)

@app.route('/submit',methods=['POST'])
def submit():

  data = request.get_json()
  #data = data.replace('\\n','\n') # this is stupid

  newhost={}
  newhost=json.loads(data)

  #print("what do we have here??\n"+str(newhost['nmap_data']))

  try:
    newhost['ip'] = get_ip(newhost['nmap_data'])
    newhost['hostname'] = get_hostname(newhost['nmap_data'])
    newhost['ports'] = str(get_ports(newhost['nmap_data']))
    #country = get_country(ip)
  except Exception as e:
    return "you fucked it up!\n"+str(traceback.format_exc())

  if len(newhost['ports']) == 0:
    return "no open ports!"

  if len(newhost['ports']) > 500:
    return "something's fuckey.."

  nweb.newhost(newhost)

  return "ip: "+newhost['ip']+"\nhostname: "+newhost['hostname']+"\nports: "+newhost['ports']

