#from django.shortcuts import render
#from django.http import HttpResponse
#from django.views.decorators.http import require_http_methods
#from django.views.decorators.csrf import csrf_exempt

#from scan_manager.models import Host
#from scan_manager.nmap_helper import * # get_ip etc

import flask
from flask import render_template
from flask import request
from flask import Flask
app = Flask(__name__,static_url_path='/static')

from netaddr import *
import time
import os
import random
import sys
import traceback

import model as nweb

# Create your views here.

@app.route('/host')
def host():
  try:
    h = request.GET['h']
    host_data = Host.objects.filter(ip=h)
  except:
    h=""
    host_data=""

  context = {
    'host': h,
    'host_data' : host_data
    }

  return render_template("host.html")

@app.route('/')
def search():

  try:
    print("potato")
    fmt=request.GET['f']
    print(fmt)
    return render_template("hostlist.html")
    #return render(request,"hostlist.html",context)
  except:
    print("boo")
    fmt=""

  return render_template("search.html")


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

@app.route('/submit')
def submit(request):

  data = str(request.body)
  data = data.replace('\\n','\n') # this is stupid

  try:
    ip = get_ip(data)
    hostname = get_hostname(data)
    ports = get_ports(data)
    country = get_country(ip)
  except Exception as e:
    return HttpResponse("you fucked it up!\n"+str(traceback.format_exc()))

  if len(ports) == 0:
    return HttpResponse("no open ports!")

  if len(ports) > 500:
    return HttpResponse("something's fuckey..")


  newhost, created=Host.objects.get_or_create(ip=ip)
  newhost.hostname = hostname
  newhost.ports = ports
  newhost.country = country
  newhost.data = request.body
  newhost.save()

  return HttpResponse("ip: "+ip+"\nhostname: "+hostname+"\nports: "+str(ports))

