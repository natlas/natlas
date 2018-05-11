import flask
from flask import render_template, request, Flask, g, url_for
from netaddr import *
import time
import os
import json
import random
import sys
import traceback
from datetime import datetime

from app import app, elastic
from .nmap_parser import NmapParser

@app.before_request
def before_request():
  g.preview_length = app.config['PREVIEW_LENGTH']

# Create your views here.
@app.route('/host')
def host():
  host = request.args.get('h')
  context = elastic.gethost(host)
  return render_template("host.html",**context)

@app.route('/')
def search():
  query = request.args.get('q', '')
  page = int(request.args.get('p', 1))
  format = request.args.get('f', "")

  searchOffset = app.config['RESULTS_PER_PAGE'] * (page-1)
  count,context = elastic.search(query,app.config['RESULTS_PER_PAGE'],searchOffset)

  next_url = url_for('search', q=query, p=page + 1) \
      if count > page * app.config['RESULTS_PER_PAGE'] else None
  prev_url = url_for('search', q=query, p=page - 1) \
      if page > 1 else None

  # what kind of output are we looking for?
  if format == 'hostlist':
    return render_template("hostlist.html",query=query, numresults=count, page=page, hosts=context)
  else:
    return render_template("search.html",query=query, numresults=count, page=page, hosts=context, next_url=next_url, prev_url=prev_url)

@app.route('/getwork')
def getwork():

  try:
    return elastic.getwork_mass()
  except:
    print("[+] Masscan data not found, selecting random target from scope.")

  random.seed(os.urandom(200))
  scope=[]
  try:
    for line in open(app.config['SCOPE_DOC']):
      try:
        scope.append(IPNetwork(line))
      except:
        print("[!] Line %s in %s failed to parse" % (line, app.config['SCOPE_DOC']))
  except:
    print("[!] Failed to find %s" % app.config['SCOPE_DOC'])
    scope=[]
    scope.append(IPNetwork("127.0.0.1"))

  blacklist=[]
  try:
    for line in open(app.config['BLACKLIST_DOC']):
      blacklist.append(IPNetwork(line))
  except Exception as e:
    print("[!] Failed to parse %s :"+str(e)[:-1]+" '"+line[:-1]+"'" % app.config['BLACKLIST_DOC'])
    blacklist=[]

  # how many hosts are in scope?
  magnitude = sum(len(network) for network in scope)
  print("[+] There are %s IPs in %s" % (magnitude, app.config['SCOPE_DOC']))

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
  nmap = NmapParser()
  data = request.get_json()

  newhost={}
  newhost=json.loads(data)
  try:
    newhost['ip'] = nmap.get_ip(newhost['nmap_data'])
    newhost['hostname'] = nmap.get_hostname(newhost['nmap_data'])
    newhost['ports'] = str(nmap.get_ports(newhost['nmap_data']))
    newhost['ctime'] = datetime.now()
  except Exception as e:
    return "[!] Couldn't find necessary nmap_data\n" + str(e)

  if len(newhost['ports']) == 0:
    return "[!] No open ports found!"

  if len(newhost['ports']) > 500:
    return "[!] More than 500 ports found. This is probably an IDS/IPS. We're going to throw the data out."

  elastic.newhost(newhost)

  return "[+] nmap successful and submitted for ip: "+newhost['ip']
