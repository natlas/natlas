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

import threading
import queue

# my script for headshotting servers
from getheadshot import getheadshot
from config import Config

import ipaddress

config = Config()
MAX_QUEUE_SIZE = int(config.max_threads) # only queue enough work for each of our active threads

RTTVAR_MSG = "RTTVAR has grown to over"

def make_request(endpoint, reqType="GET", postData=None, contentType="application/json", statusCode=200):
    try:
        if reqType == "GET":
            req = requests.get(config.server+endpoint, timeout=config.request_timeout)
            if req.status_code != statusCode:
                print("[!] Expected %s, received %s" % (statusCode, req.status_code))
                return False
            if req.headers['content-type'] != contentType:
                print("[!] Expected %s, received %s" % (contentType, req.headers['content-type']))
                return False
        elif reqType == "POST" and postData:
            req = requests.post(config.server+endpoint, json=postData, timeout=config.request_timeout)
            if req.status_code != statusCode:
                print("[!] Expected %s, received %s" % (statusCode, req.status_code))
                return False
    except requests.ConnectionError as e:
        print("[!] Connection Error connecting to %s." % config.server)
        return False
    except requests.Timeout as e:
        print("[!] Request timed out after %s seconds." % config.request_timeout)
        return False
    except ValueError as e:
        print("[!] Error: %s" % e)
        return False

    return req

def backoff_request(*args, **kwargs):
    attempt = 0
    result = None
    while not result:
        result = make_request(*args, **kwargs)
        if not result:
            attempt += 1
            jitter = random.randint(0,1000) / 1000 # jitter to reduce chance of locking
            current_sleep = min(config.backoff_max, config.backoff_base * 2 ** attempt) + jitter
            print("[!] Request to %s failed. Waiting %s seconds before retrying." % (config.server, current_sleep))
            time.sleep(current_sleep)
    return result

def get_services_file():
    print("[+] Fetching natlas-services file from %s" % config.server)
    response = backoff_request(endpoint="/api/natlas-services")
    if response:
        serviceData = response.json()
        if serviceData["id"] == "None":
            print("[!] Error: %s doesn't have a service file for us" % config.server)
            return False
        if not hashlib.sha256(serviceData["services"].encode()).hexdigest() == serviceData["sha256"]:
            print("[!] Error: hash provided by %s doesn't match locally computed hash of services" % config.server)
            return False
        with open("natlas-services", "w") as f:
            f.write(serviceData["services"])
        with open("natlas-services", "r") as f:
            if not hashlib.sha256(f.read().rstrip('\r\n').encode()).hexdigest() == serviceData["sha256"]:            
                print("[!] Error: hash of local file doesn't match hash provided by server")
                return False
    else:
        return False # return false if we were unable to get a response from the server
    return serviceData["sha256"] # return True if we got a response and everything checks out


def fetch_target():
    print("[+] Fetching Target from %s" % config.server)
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
            print("[!] We're not configured to scan local addresses!")
            return False
    except ipaddress.AddressValueError:
        print("[!] %s is not a valid IP Address" % target)
        return False
    return True

def generate_scan_id():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))

def scan(target=None, scan_id=None):
    
    if not validate_target(target):
        print("[!] Failed to validate target %s" % target)
        return False
    print("[+] Target: %s" % target)
    print("[+] Scan ID: %s" % scan_id)

    command = ["nmap", "-oA", "data/natlas."+scan_id, "-sV", "-O","-sC", "-open", "--servicedb", "./natlas-services", target]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        out, err = process.communicate(timeout=config.scan_timeout)  # 6 minutes
    except:
        try:
            print("[+] (%s) Killing slacker process" % scan_id)
            process.kill()
        except:
            pass

    print("[+] Scan Complete: " + scan_id)

    result = {}
    result['scan_id'] = scan_id
    for ext in 'nmap', 'gnmap', 'xml':
        result[ext+"_data"] = open("data/natlas."+scan_id+"."+ext).read()
        os.remove("data/natlas."+scan_id+"."+ext)
        print("[+] (%s) Cleaning up: natlas.%s.%s" % (scan_id, scan_id, ext))

    if len(result['nmap_data']) < 250:
        print("[!] (%s) Nmap data is too short" % scan_id)
        return
    elif 'Nmap scan report for' not in result['nmap_data']: # checking for this on the agent saves bandwidth
        print("[!] (%s) Nmap scan report not found" % scan_id)
        return
    else:
        print("[+] (%s) scan size: %s" % (scan_id, len(result['nmap_data'])))

    if RTTVAR_MSG in result['nmap_data']:
        orig_data = result['nmap_data'].splitlines()
        new_data = ''
        for line in orig_data:
            if line.startswith(RTTVAR_MSG):
                continue
            else:
                new_data += line + '\n'
        result['nmap_data'] = new_data.rstrip('\n')

    if shutil.which("aquatone") is not None:
        if "80/tcp" in result['nmap_data']:
            if getheadshot(target, scan_id, 'http') is True:
                screenshotPath = "data/aquatone." + scan_id + ".http/screenshots/http__" +target.replace('.','_') + ".png"
                if not os.path.isfile(screenshotPath):
                    shutil.rmtree("data/aquatone." + scan_id + ".http/")
                else:
                    result['httpheadshot'] = str(base64.b64encode(
                        open(screenshotPath, 'rb').read()))[2:-1]
                    shutil.rmtree("data/aquatone." + scan_id + ".http/")
                    print("[+] (%s) HTTP snapshot acquired" % scan_id)
            else:
                print("[!] (%s) Failed to acquire HTTP snapshot" % scan_id)
        if "443/tcp" in result['nmap_data']:
            if getheadshot(target, scan_id, 'https') is True:
                screenshotPath = "data/aquatone." + scan_id + ".https/screenshots/https__" +target.replace('.','_') + ".png"
                if not os.path.isfile(screenshotPath):
                    shutil.rmtree("data/aquatone." + scan_id + ".https/")
                else:
                    result['httpsheadshot'] = str(base64.b64encode(
                        open(screenshotPath, 'rb').read()))[2:-1]
                    shutil.rmtree("data/aquatone." + scan_id + ".https/")
                    print("[+] (%s) HTTPS snapshot acquired" % scan_id)
            else:
                print("[!] (%s) Failed to acquire HTTPS snapshot" % scan_id)
    if shutil.which("vncsnapshot") is not None:
        if "5900/tcp" in result['nmap_data']:
            if getheadshot(target, scan_id, 'vnc') is True:
                result['vncsheadshot'] = str(base64.b64encode(
                    open("data/natlas."+scan_id+".vnc.headshot.jpg", 'rb').read()))[2:-1]
                os.remove("data/natlas."+scan_id+".vnc.headshot.jpg")
                print("[+] (%s) VNC snapshot acquired" % scan_id)
            else:
                print("[!] (%s) Failed to acquire VNC snapshot" % scan_id)

    # submit result
    print("[+] (%s) Submitting work" % scan_id)
    response = backoff_request(endpoint="/api/submit", reqType="POST", postData=json.dumps(result))
    print("[+] (%s) Response: %s" % (scan_id, response.status_code))

class ThreadScan(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            target_data = self.queue.get()
            scan(target_data["target"], target_data["scan_id"])
            self.queue.task_done()

def main():
    if not os.path.isdir("data"):
        os.mkdir("data")

    PARSER_DESC = "Scan hosts and report data to a configured server. The server will reject your findings if they are deemed not in scope."
    PARSER_EPILOG = "Report problems to https://github.com/natlas/natlas"
    parser = argparse.ArgumentParser(description=PARSER_DESC, epilog=PARSER_EPILOG)
    mutually_exclusive = parser.add_mutually_exclusive_group()
    mutually_exclusive.add_argument('--target', metavar='IPADDR', help="An IPv4 address or CIDR range to scan. e.g. 192.168.0.1, 192.168.0.1/24", dest='target')
    mutually_exclusive.add_argument('--target-file', metavar='FILENAME', help="A file of line separated target IPv4 addresses or CIDR ranges", dest='tfile')
    args = parser.parse_args()
    
    q = queue.Queue(maxsize=MAX_QUEUE_SIZE)

    servicesSha = ""

    if os.path.isfile("natlas-services"):
        servicesSha = hashlib.sha256(open("natlas-services", "r").read().rstrip('\r\n').encode()).hexdigest()
    else:
        servicesSha = get_services_file()
        if not servicesSha:
            print("[!] Failed to get valid services file from %s" % config.server)
            return False

    # Start threads that will wait for items in queue and then scan them
    for i in range(int(config.max_threads)):
        t = ThreadScan(q)
        t.setDaemon(True)
        t.start()

    if args.target:
        print("[+] Scanning: %s" % args.target)

        targetNetwork = ipaddress.ip_interface(args.target)
        if targetNetwork.with_prefixlen.endswith('/32'):
            scan_id = generate_scan_id()
            target_data = {"target": str(targetNetwork.ip), "scan_id": scan_id}
            q.put(target_data)
        else:    
            # Iterate over usable hosts in target, queue.put will block until a queue slot is available
            for t in targetNetwork.network.hosts(): 
                scan_id = generate_scan_id()
                target_data = {"target": str(t), "scan_id": scan_id}
                q.put(target_data)

        q.join()
        print("[+] Finished scanning: %s" % args.target)
        return

    elif args.tfile:
        print("[+] Reading scope from file: %s" % args.tfile)

        for target in open(args.tfile, "r"):
            targetNetwork = ipaddress.ip_interface(target.strip())
            if targetNetwork.with_prefixlen.endswith('/32'):
                scan_id = generate_scan_id()
                target_data = {"target": str(targetNetwork.ip), "scan_id": scan_id}
                q.put(target_data)
            else:
                for t in targetNetwork.network.hosts():
                    scan_id = generate_scan_id()
                    target_data = {"target": str(t), "scan_id": scan_id}
                    q.put(target_data)
        q.join()
        print("[+] Finished scanning the target file %s" % args.tfile)
        return

    # This is the default behavior of fetching work from the server
    else:
        while True:
            target_data = fetch_target()
            if target_data["services_hash"] != servicesSha:
                servicesSha = get_services_file()
                if not servicesSha:
                    print("Failed to get updated services from %s" % config.server)

            q.put(target_data)


if __name__ == "__main__":
    main()
