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

import threading
import queue

# my script for headshotting servers
from getheadshot import getheadshot
from config import Config

import ipaddress

config = Config()
MAX_QUEUE_SIZE = 100 # setting max queue size to 100 so that we can take advantage of the memory benefits of using the .hosts() iterator instead of loading all hosts into a queue

def fetch_target():
    print("[+] Fetching Target from %s" % config.server)
    try:
        target_request = requests.get(config.server+"/getwork", timeout=config.request_timeout)
        if target_request.status_code != requests.codes.ok:
            print("[!] Server returned %s" % target_request.status_code)
            return False
        if target_request.headers['content-type'] != "application/json":
            print("[!] Expected application/json, received %s" % target_request.headers['content-type'])
            return False
        target_data = target_request.json()
    except requests.ConnectionError as e:
        print("[!] Connection Error connecting to %s." % config.server)
        return False
    except requests.Timeout as e:
        print("[!] Request timed out after %s seconds." % config.request_timeout)
        return False
    except ValueError as e:
        print("[!] Error: %s" % e)
        return False
    target = target_data["target"]
    scan_id = target_data["scan_id"]

    return target, scan_id

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

def scan(target=None):
    attempt = 0
    scan_id = False
    while not target:
        target, scan_id = fetch_target()
        if not target:
            attempt += 1
            jitter = random.randint(0,1000) / 1000 # jitter to reduce chance of locking
            current_sleep = min(config.backoff_max, config.backoff_base * 2 ** attempt) + jitter
            print("[!] Failed to acquire target from %s. Waiting %s seconds before retrying." % (config.server, current_sleep))
            time.sleep(current_sleep)
    
    if not validate_target(target):
        print("[!] Failed to validate target %s" % target)
        return False
    print("[+] Target: %s" % target)

    if not scan_id: # If running in standalone mode, generate our own scan_id
        scan_id = ''.join(random.choice(string.ascii_lowercase + string.digits)
               for _ in range(10))
    print("[+] Scan ID: %s" % scan_id)

    command = ["nmap", "-oA", "data/natlas."+scan_id, "-sV", "-O","-sC", "-open", target]

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

    if shutil.which("aquatone") is not None:
        if "80/tcp" in result['nmap_data']:
            if getheadshot(target, scan_id, 'http') is True:
                screenshotPath = "data/aquatone." + scan_id + ".http/screenshots/http__" +target.replace('.','_') + ".png"
                if not os.path.isfile(screenshotPath):
                    pass
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
                    pass
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
    response = requests.post(config.server+"/submit", json=json.dumps(result)).text
    print("[+] (%s) Response:\n%s" % (scan_id, response))

class ThreadScan(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            target = self.queue.get()
            scan(target)
            self.queue.task_done()

def main():
    if not os.path.isdir("data"):
        os.mkdir("data")

    PARSER_DESC = "Scan hosts and report data to a configured server. The server will reject your findings if they are deemed not in scope."
    PARSER_EPILOG = "Report problems to https://github.com/natlas/natlas"
    parser = argparse.ArgumentParser(description=PARSER_DESC, epilog=PARSER_EPILOG)
    mutually_exclusive = parser.add_mutually_exclusive_group()
    mutually_exclusive.add_argument('--target', metavar='IPADDR', help="An IPv4 address to scan. e.g. 192.168.0.1", dest='target')
    mutually_exclusive.add_argument('--range', metavar='CIDR', help="A CIDR block to scan. e.g. 192.168.0.0/24", dest='range')
    mutually_exclusive.add_argument('--target-file', metavar='FILENAME', help="A file of line separated target IPv4 addresses", dest='tfile')
    mutually_exclusive.add_argument('--range-file', metavar='FILENAME', help="A file of line separated target CIDR blocks", dest='rfile')
    args = parser.parse_args()
    
    if args.target:
        print("[+] Running in single-target mode")
        scan(args.target)
        
        print("[+] Finished scanning the single target: %s" % args.target)
        return

    elif args.range:
        print("[+] Running in target-range mode\n[+] Target Range: %s" % args.range)
        targetNetwork = ipaddress.ip_network(args.range, False)
        q = queue.Queue(maxsize=MAX_QUEUE_SIZE)

        # Start threads that will wait for items in queue and then scan them
        for i in range(config.max_threads):
            t = ThreadScan(q)
            t.setDaemon(True)
            t.start()

        # Iterate over items in target, queue.put will block until a queue slot is available
        for target in targetNetwork.hosts(): 
            q.put(str(target))

        # queue.join to wait until the queue is processed once we've finished stuffing hosts into the queue
        q.join()
        print("[+] Finished scanning the target range %s" % args.range)
        return

    elif args.tfile:
        print("[+] Running in target-file mode\n[+] Target File: %s" % args.tfile)
        q = queue.Queue(maxsize=MAX_QUEUE_SIZE)

        for i in range(config.max_threads):
            t = ThreadScan(q)
            t.setDaemon(True)
            t.start()

        for target in open(args.tfile, "r"):
            q.put(str(target.strip()))
        
        q.join()
        print("[+] Finished scanning the target file %s" % args.tfile)
        return

    elif args.rfile:
        print("[+] Running in range-file mode\n[+] Range File: %s" % args.rfile)
        q = queue.Queue(maxsize=MAX_QUEUE_SIZE)

        for i in range(config.max_threads):
            t = ThreadScan(q)
            t.setDaemon(True)
            t.start()

        for trange in open(args.rfile, "r"):
            targetNetwork = ipaddress.ip_network(trange.strip())
            for target in targetNetwork.hosts():
                q.put(str(target))

        q.join()
        print("[+] Finished scanning the range file %s" % args.rfile)
        return
    # This is the default behavior of fetching work from the server
    else:
        while True:
            if threading.active_count() <= config.max_threads:
                notifylock = False
                print("[+] Active Threads: %s" % threading.active_count())
                t = threading.Thread(target=scan)
                t.start()
            else:
                if notifylock is False:
                    print("[+] Thread pool exhausted")
                notifylock = True
            time.sleep(1) 


if __name__ == "__main__":
    main()
