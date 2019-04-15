#!/usr/bin/env python3

import sys
import requests
import subprocess
import time
import os
import random
import string
import json
import base64
import argparse
import shutil
import hashlib
import glob
from datetime import datetime,timezone
from libnmap.parser import NmapParser, NmapParserException
import ipaddress
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import threading
import queue


# my script for headshotting servers
from getheadshot import getheadshot
from config import Config

ERR = {"INVALIDTARGET":1,"SCANTIMEOUT":2, "DATANOTFOUND":3, "INVALIDDATA": 4}
AGENT_VERSION="0.6.0"

config = Config()
MAX_QUEUE_SIZE = int(config.max_threads) # only queue enough work for each of our active threads

RTTVAR_MSG = "RTTVAR has grown to over"


def print_err(message):
    threadname = threading.current_thread().name
    print("[!] %s: %s" % (threadname, message))

def print_info(message):
    threadname = threading.current_thread().name
    print("[+] %s: %s" % (threadname, message))

if config.ignore_ssl_warn:
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
def make_request(endpoint, reqType="GET", postData=None, contentType="application/json", statusCode=200):
    headers = {'user-agent': 'natlas-agent/{}'.format(AGENT_VERSION)}
    if config.agent_id and config.auth_token:
        authheader = config.agent_id + ":" + config.auth_token
        headers['Authorization'] = 'Bearer {}'.format(authheader)
    try:
        if reqType == "GET":
            req = requests.get(config.server+endpoint, timeout=config.request_timeout, headers=headers, verify=(not config.ignore_ssl_warn))
            if req.status_code == 403:
                print_err("Unauthorized request, please set NATLAS_AGENT_TOKEN to your authorization token and restart the script")
                os._exit(403)
            if req.status_code != statusCode:
                print_err("Expected %s, received %s" % (statusCode, req.status_code))
                return False
            if req.headers['content-type'] != contentType:
                print_err("Expected %s, received %s" % (contentType, req.headers['content-type']))
                return False
        elif reqType == "POST" and postData:
            req = requests.post(config.server+endpoint, json=postData, timeout=config.request_timeout, headers=headers, verify=(not config.ignore_ssl_warn))
            if req.status_code != statusCode:
                print_err("Expected %s, received %s" % (statusCode, req.status_code))
                return False
    except requests.ConnectionError as e:
        print_err("Connection Error connecting to %s" % config.server)
        return False
    except requests.Timeout as e:
        print_err("Request timed out after %s seconds." % config.request_timeout)
        return False
    except ValueError as e:
        print_err("Error: %s" % e)
        return False

    return req

def backoff_request(giveup=False, *args, **kwargs):
    attempt = 0
    result = None
    while not result:
        result = make_request(*args, **kwargs)
        if not result:
            attempt += 1
            if giveup and attempt == config.max_retries:
                print_err("Request to %s failed %s times. Giving up" % (config.server, config.max_retries))
                return None
            jitter = random.randint(0,1000) / 1000 # jitter to reduce chance of locking
            current_sleep = min(config.backoff_max, config.backoff_base * 2 ** attempt) + jitter
            print_err("Request to %s failed. Waiting %s seconds before retrying." % (config.server, current_sleep))
            time.sleep(current_sleep)
    return result

def get_services_file():
    print_info("Fetching natlas-services file from %s" % config.server)
    response = backoff_request(endpoint="/api/natlas-services")
    if response:
        serviceData = response.json()
        if serviceData["id"] == "None":
            print_err("%s doesn't have a service file for us" % config.server)
            return False
        if not hashlib.sha256(serviceData["services"].encode()).hexdigest() == serviceData["sha256"]:
            print_err("hash provided by %s doesn't match locally computed hash of services" % config.server)
            return False
        with open("natlas-services", "w") as f:
            f.write(serviceData["services"])
        with open("natlas-services", "r") as f:
            if not hashlib.sha256(f.read().rstrip('\r\n').encode()).hexdigest() == serviceData["sha256"]:            
                print_err("hash of local file doesn't match hash provided by server")
                return False
    else:
        return False # return false if we were unable to get a response from the server
    return serviceData["sha256"] # return True if we got a response and everything checks out


def fetch_target():
    print_info("Fetching Target from %s" % config.server)
    response = backoff_request(endpoint="/api/getwork")
    if response:
        target_data = response.json()
    else:
        return False # failed to fetch target from server
    return target_data

def validate_target(target):
    try:
        iptarget = ipaddress.ip_address(target)
        if iptarget.is_private and not config.scan_local:
            print_err("We're not configured to scan local addresses!")
            return False
    except ipaddress.AddressValueError:
        print_err("%s is not a valid IP Address" % target)
        return False
    return True

def generate_scan_id():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))

def cleanup_files(scan_id):
    print_info("Cleaning up files for %s" % scan_id)
    for file in glob.glob("data/*."+scan_id+".*"):
        os.remove(file)

def scan(target_data=None):
    
    if not validate_target(target_data["target"]):
        return ERR["INVALIDTARGET"]
    print_info("Target: %s" % target_data["target"])
    
    result = {}

    # If agent authentication is required, this agent id has to match a server side agent id
    # If it's not required and an agent_id is set, we'll use that in scan data
    # If it's not required and an agent_id is not set, we'll consider it an anonymous scan.
    if config.agent_id: 
        result['agent'] = config.agent_id
    else:
        result['agent'] = "anonymous"
    
    target = target_data["target"]
    result['ip'] = target
    result['scan_reason'] = target_data['scan_reason']
    result['tags'] = target_data['tags']
    scan_id = target_data["scan_id"]
    result['scan_id'] = scan_id
    agentConfig = target_data["agent_config"]
    result['scan_start'] = datetime.now(timezone.utc).isoformat()

    command = ["nmap", "-oA", "data/natlas."+scan_id, "--servicedb", "./natlas-services"]
    if agentConfig["versionDetection"]:
        command.append("-sV")
    if agentConfig["osDetection"]:
        command.append("-O")
    if agentConfig["defaultScripts"]:
        command.append("-sC")
    if agentConfig["onlyOpens"]:
        command.append("--open")
    command.append(target_data["target"])

    TIMEDOUT = False
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        out, err = process.communicate(timeout=int(agentConfig["scanTimeout"]))
    except:
        try:
            print_err("Scan %s timed out" % scan_id)
            process.kill()
            TIMEDOUT = True
        except:
            pass

    if TIMEDOUT:
        result['is_up'] = False
        result['port_count'] = 0
        result['scan_stop'] = datetime.now(timezone.utc).isoformat()
        result['timed_out'] = True
        cleanup_files(scan_id)
        print_info("Submitting scan timeout notice for %s" % result['ip'])
        response = backoff_request(giveup=True, endpoint="/api/submit", reqType="POST", postData=json.dumps(result))
        return
    else:
        print_info("Scan  %s Complete" % scan_id)

    for ext in 'nmap', 'gnmap', 'xml':
        try: 
            result[ext+"_data"] = open("data/natlas."+scan_id+"."+ext).read()
        except:
            print_err("Couldn't read natlas.%s.%s" % (scan_id, ext))
            return ERR["DATANOTFOUND"]

    nmap_report = NmapParser.parse(result['xml_data'])

    if nmap_report.hosts_total < 1:
        print_err("No hosts found in scan data")
        return "[!] No hosts found in scan data"
    elif nmap_report.hosts_total > 1:
        print_err("Too many hosts found in scan data")
        return "[!] Too many hosts found in scan data"
    elif nmap_report.hosts_down == 1:
        # host is down
        result['is_up'] = False
        result['port_count'] = 0
        result['scan_stop'] = datetime.now(timezone.utc).isoformat()
        cleanup_files(scan_id)
        print_info("Submitting host down notice for %s" % (result['ip']))
        response = backoff_request(giveup=True, endpoint="/api/submit", reqType="POST", postData=json.dumps(result))
        return
    elif nmap_report.hosts_up == 1 and len(nmap_report.hosts) == 0:
        # host is up but no reportable ports were found
        result['is_up'] = True
        result['port_count'] = 0
        result['scan_stop'] = datetime.now(timezone.utc).isoformat()
        cleanup_files(scan_id)
        print_info("Submitting %s ports for %s" % (result['port_count'], result['ip']))
        response = backoff_request(giveup=True, endpoint="/api/submit", reqType="POST", postData=json.dumps(result))
        return
    else:
        # host is up and reportable ports were found
        result['is_up'] = nmap_report.hosts[0].is_up()
        result['port_count'] = len(nmap_report.hosts[0].get_ports())

    if target_data["agent_config"]["webScreenshots"] and shutil.which("aquatone") is not None:
        if "80/tcp" in result['nmap_data']:
            if getheadshot(target, scan_id, 'http') is True:
                print_info("Attempting to take HTTP screenshot for %s" % result['ip'])
                screenshotPath = "data/aquatone." + scan_id + ".http/screenshots/http__" +target.replace('.','_') + ".png"
                if not os.path.isfile(screenshotPath):
                    shutil.rmtree("data/aquatone." + scan_id + ".http/")
                else:
                    result['httpheadshot'] = str(base64.b64encode(
                        open(screenshotPath, 'rb').read()))[2:-1]
                    shutil.rmtree("data/aquatone." + scan_id + ".http/")
                    print_info("HTTP screenshot acquired for %s" % result['ip'])
            else:
                print_err("Failed to acquire HTTP screenshot for %s" % result['ip'])

        if "443/tcp" in result['nmap_data']:
            if getheadshot(target, scan_id, 'https') is True:
                print_info("Attempting to take HTTPS screenshot for %s" % result['ip'])
                screenshotPath = "data/aquatone." + scan_id + ".https/screenshots/https__" +target.replace('.','_') + ".png"
                if not os.path.isfile(screenshotPath):
                    shutil.rmtree("data/aquatone." + scan_id + ".https/")
                else:
                    result['httpsheadshot'] = str(base64.b64encode(
                        open(screenshotPath, 'rb').read()))[2:-1]
                    shutil.rmtree("data/aquatone." + scan_id + ".https/")
                    print_info("HTTPS screenshot acquired for %s" % result['ip'])
            else:
                print_err("Failed to acquire HTTPS screenshot for %s" % result['ip'])

    if target_data["agent_config"]["vncScreenshots"] and shutil.which("vncsnapshot") is not None:
        if "5900/tcp" in result['nmap_data']:
            print_info("Attempting to take vnc screenshot for %s" % result['ip'])
            if getheadshot(target, scan_id, 'vnc') is True:
                result['vncsheadshot'] = str(base64.b64encode(
                    open("data/natlas."+scan_id+".vnc.headshot.jpg", 'rb').read()))[2:-1]
                os.remove("data/natlas."+scan_id+".vnc.headshot.jpg")
                print_info("VNC screenshot acquired for %s" % result['ip'])
            else:
                print_err("Failed to acquire screenshot for %s" % result['ip'])

    # submit result
    result['scan_stop'] = datetime.now(timezone.utc).isoformat()
    cleanup_files(scan_id)
    print_info("Submitting %s ports for %s" % (result['port_count'], result['ip']))
    response = backoff_request(giveup=True, endpoint="/api/submit", reqType="POST", postData=json.dumps(result))
    if not response:
        print_err("Something went wrong submitting results for %s" % result['ip'])
    else:
        print_info("Response: %s" % (response.text))

class ThreadScan(threading.Thread):
    def __init__(self, queue, auto=False, servicesSha=''):
        threading.Thread.__init__(self)
        self.queue = queue
        self.auto = auto
        self.servicesSha = servicesSha

    def run(self):
        # If we're in auto mode, the threads handle getting work from the server
        if self.auto:
            while True: 
                target_data = fetch_target()
                if target_data["services_hash"] != self.servicesSha:
                    self.servicesSha = get_services_file()
                    if not self.servicesSha:
                        print_err("Failed to get updated services from %s" % config.server)
                result = scan(target_data)
        
        else:
            #If we're not in auto mode, then the queue is populated with work from local data
            target_data = self.queue.get()
            result = scan(target_data)
            self.queue.task_done()

def main():
    if not os.geteuid() == 0:
        raise SystemExit("Please run as a privileged user in order to use nmap's features.")
    if not os.path.isdir("data"):
        os.mkdir("data")

    PARSER_DESC = "Scan hosts and report data to a configured server. The server will reject your findings if they are deemed not in scope."
    PARSER_EPILOG = "Report problems to https://github.com/natlas/natlas"
    parser = argparse.ArgumentParser(description=PARSER_DESC, epilog=PARSER_EPILOG, prog='natlas-agent')
    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(AGENT_VERSION))
    mutually_exclusive = parser.add_mutually_exclusive_group()
    mutually_exclusive.add_argument('--target', metavar='IPADDR', help="An IPv4 address or CIDR range to scan. e.g. 192.168.0.1, 192.168.0.1/24", dest='target')
    mutually_exclusive.add_argument('--target-file', metavar='FILENAME', help="A file of line separated target IPv4 addresses or CIDR ranges", dest='tfile')
    args = parser.parse_args()
    
    autoScan = True
    if args.target or args.tfile:
        autoScan = False

    q = queue.Queue(maxsize=MAX_QUEUE_SIZE)

    servicesSha = ""
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    SERVICESPATH = os.path.join(BASEDIR, "natlas-services")
    if os.path.isfile(SERVICESPATH):
        servicesSha = hashlib.sha256(open(SERVICESPATH, "r").read().rstrip('\r\n').encode()).hexdigest()
    else:
        servicesSha = get_services_file()
        if not servicesSha:
            raise SystemExit("[!] Failed to get valid services file from %s" % config.server)

    # Start threads that will wait for items in queue and then scan them
    for i in range(int(config.max_threads)):
        t = ThreadScan(q, autoScan, servicesSha)
        t.setDaemon(True)
        t.start()

    # Use a default agent config of all options enabled if we are in standalone mode
    defaultAgentConfig = {"id": 0, "versionDetection": True, "osDetection": True, "defaultScripts": True, "onlyOpens": True, "scanTimeout": 300, "webScreenshots": True, "vncScreenshots": True}
    if args.target:
        print_info("Scanning: %s" % args.target)

        targetNetwork = ipaddress.ip_interface(args.target)
        if targetNetwork.with_prefixlen.endswith('/32'):
            scan_id = generate_scan_id()
            target_data = {"target": str(targetNetwork.ip), "scan_id": scan_id, "agent_config":defaultAgentConfig}
            q.put(target_data)
        else:    
            # Iterate over usable hosts in target, queue.put will block until a queue slot is available
            for t in targetNetwork.network.hosts(): 
                scan_id = generate_scan_id()
                target_data = {"target": str(t), "scan_id": scan_id, "agent_config":defaultAgentConfig}
                q.put(target_data)

        q.join()
        print_info("Finished scanning: %s" % args.target)
        return

    elif args.tfile:
        print_info("Reading scope from file: %s" % args.tfile)

        for target in open(args.tfile, "r"):
            targetNetwork = ipaddress.ip_interface(target.strip())
            if targetNetwork.with_prefixlen.endswith('/32'):
                scan_id = generate_scan_id()
                target_data = {"target": str(targetNetwork.ip), "scan_id": scan_id, "agent_config":defaultAgentConfig}
                q.put(target_data)
            else:
                for t in targetNetwork.network.hosts():
                    scan_id = generate_scan_id()
                    target_data = {"target": str(t), "scan_id": scan_id, "agent_config":defaultAgentConfig}
                    q.put(target_data)
        q.join()
        print_info("Finished scanning the target file %s" % args.tfile)
        return

    # This is the default behavior of fetching work from the server
    else:
        while True:
            time.sleep(60)


if __name__ == "__main__":
    main()
