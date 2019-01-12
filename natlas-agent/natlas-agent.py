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

def scan(target=None):
    server = config.server
    if target is None:
        print("[+] Fetching Target from %s" % server)
        target_data = json.loads(requests.get(server+"/getwork").text)
        target = target_data["target"]

    print("[+] Target: "+target)

    # scan server
    rand = ''.join(random.choice(string.ascii_lowercase + string.digits)
                   for _ in range(10))
    print("[+] Scan ID: "+rand)

    command = ["nmap", "-oA", "data/natlas."+rand, "-sV", "-O","-sC", "-open", target]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    try:
        out, err = process.communicate(timeout=config.timeout)  # 6 minutes
    except:
        try:
            print("[+] (%s) Killing slacker process" % rand)
            process.kill()
        except:
            pass

    print("[+] Scan Complete: " + rand)

    result = {}
    result['scan_id'] = rand
    for ext in 'nmap', 'gnmap', 'xml':
        result[ext+"_data"] = open("data/natlas."+rand+"."+ext).read()
        os.remove("data/natlas."+rand+"."+ext)
        print("[+] (%s) Cleaning up: natlas.%s.%s" % (rand, rand, ext))

    if len(result['nmap_data']) < 250:
        print("[!] (%s) Nmap data is too short" % rand)
        return
    elif 'Nmap scan report for' not in result['nmap_data']: # checking for this on the agent saves bandwidth
        print("[!] (%s) Nmap scan report not found" % rand)
        return
    else:
        print("[+] (%s) scan size: %s" % (rand, len(result['nmap_data'])))

    if shutil.which("aquatone") is not None:
        if "80/tcp" in result['nmap_data']:
            if getheadshot(target, rand, 'http') is True:
                screenshotPath = "data/aquatone." + rand + ".http/screenshots/http__" +target.replace('.','_') + ".png"
                if not os.path.isfile(screenshotPath):
                    pass
                else:
                    result['httpheadshot'] = str(base64.b64encode(
                        open(screenshotPath, 'rb').read()))[2:-1]
                    shutil.rmtree("data/aquatone." + rand + ".http/")
                    print("[+] (%s) HTTP snapshot acquired" % rand)
            else:
                print("[!] (%s) Failed to acquire HTTP snapshot" % rand)
        if "443/tcp" in result['nmap_data']:
            if getheadshot(target, rand, 'https') is True:
                screenshotPath = "data/aquatone." + rand + ".https/screenshots/https__" +target.replace('.','_') + ".png"
                if not os.path.isfile(screenshotPath):
                    pass
                else:
                    result['httpsheadshot'] = str(base64.b64encode(
                        open(screenshotPath, 'rb').read()))[2:-1]
                    shutil.rmtree("data/aquatone." + rand + ".https/")
                    print("[+] (%s) HTTPS snapshot acquired" % rand)
            else:
                print("[!] (%s) Failed to acquire HTTPS snapshot" % rand)
    if shutil.which("vncsnapshot") is not None:
        if "5900/tcp" in result['nmap_data']:
            if getheadshot(target, rand, 'vnc') is True:
                result['vncsheadshot'] = str(base64.b64encode(
                    open("data/natlas."+rand+".vnc.headshot.jpg", 'rb').read()))[2:-1]
                os.remove("data/natlas."+rand+".vnc.headshot.jpg")
                print("[+] (%s) VNC snapshot acquired" % rand)
            else:
                print("[!] (%s) Failed to acquire VNC snapshot" % rand)

    # submit result
    print("[+] (%s) Submitting work" % rand)
    response = requests.post(server+"/submit", json=json.dumps(result)).text
    print("[+] (%s) Response:\n%s" % (rand, response))

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
