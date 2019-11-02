#!/usr/bin/env python3

import subprocess
import time
import os
import argparse
import hashlib
import ipaddress
import queue

from natlas import logging, error_reporting
from config import Config
from natlas.threadscan import ThreadScan
from natlas.net import NatlasNetworkServices

ERR = {"INVALIDTARGET": 1, "SCANTIMEOUT": 2, "DATANOTFOUND": 3, "INVALIDDATA": 4}

config = Config()
MAX_QUEUE_SIZE = int(config.max_threads) # only queue enough work for each of our active threads

global_logger = logging.get_logger("MainThread")
netsrv = NatlasNetworkServices(config)


def add_targets_to_queue(target, q):
	targetNetwork = ipaddress.ip_interface(target.strip())
	if targetNetwork.with_prefixlen.endswith('/32'):
		target_data = netsrv.get_work(target=str(targetNetwork.ip))
		if not target_data:
			return
		q.put(target_data)
	else:
		# Iterate over usable hosts in target, queue.put will block until a queue slot is available
		for t in targetNetwork.network.hosts():
			target_data = netsrv.get_work(target=str(t))
			if not target_data:
				continue
			q.put(target_data)


def main():

	PARSER_DESC = "Scan hosts and report data to a configured server. The server will reject your findings if they are deemed not in scope."
	PARSER_EPILOG = "Report problems to https://github.com/natlas/natlas"
	parser = argparse.ArgumentParser(description=PARSER_DESC, epilog=PARSER_EPILOG, prog='natlas-agent')
	parser.add_argument('--version', action='version', version='%(prog)s {}'.format(config.NATLAS_VERSION))
	mutually_exclusive = parser.add_mutually_exclusive_group()
	mutually_exclusive.add_argument('--target', metavar='IPADDR', help="An IPv4 address or CIDR range to scan. e.g. 192.168.0.1, 192.168.0.1/24", dest='target')
	mutually_exclusive.add_argument('--target-file', metavar='FILENAME', help="A file of line separated target IPv4 addresses or CIDR ranges", dest='tfile')
	args = parser.parse_args()

	# Check if Nmap has required capabilities to run as a non-root user
	try:
		nmap_path = subprocess.check_output(["which", "nmap"]).decode("utf-8").strip() # nosec
		nmap_caps = subprocess.check_output(["getcap", nmap_path]).decode("utf-8") # nosec
	except subprocess.CalledProcessError:
		msg = "Couldn't find nmap"
		global_logger.critical(msg)
		raise SystemExit("[!] %s" % msg)

	needed_caps = ["cap_net_raw", "cap_net_admin", "cap_net_bind_service"]
	missing_caps = [cap for cap in needed_caps if cap not in nmap_caps]
	if missing_caps:
		msg = "Missing Nmap capabilities: %s" % " ".join(missing_caps)
		global_logger.critical(msg)
		raise SystemExit("[!] %s" % msg)

	required_dirs = ['data', 'logs', 'tmp']
	for directory in required_dirs:
		if not os.path.isdir(directory):
			os.mkdir(directory)

	autoScan = True
	if args.target or args.tfile:
		autoScan = False

	# Initialize SentryIo after basic environment checks complete
	error_reporting.initialize_sentryio(config)
	q = queue.Queue(maxsize=MAX_QUEUE_SIZE)

	servicesSha = ""
	BASEDIR = os.path.abspath(os.path.dirname(__file__))
	SERVICESPATH = os.path.join(BASEDIR, "tmp", "natlas-services")
	if os.path.isfile(SERVICESPATH):
		servicesSha = hashlib.sha256(open(SERVICESPATH, "r").read().rstrip('\r\n').encode()).hexdigest()
	else:
		servicesSha = netsrv.get_services_file()
		if not servicesSha:
			raise SystemExit("[!] Failed to get valid services file from %s" % config.server)

	# Start threads that will wait for items in queue and then scan them
	for i in range(int(config.max_threads)):
		t = ThreadScan(q, config, autoScan, servicesSha)
		t.setDaemon(True)
		t.start()

	if args.target:
		global_logger.info("Scanning: %s" % args.target)
		add_targets_to_queue(args.target, q)
		q.join()
		global_logger.info("Finished scanning: %s" % args.target)
		return

	elif args.tfile:
		global_logger.info("Reading scope from file: %s" % args.tfile)
		for target in open(args.tfile, "r"):
			add_targets_to_queue(target, q)
		q.join()
		global_logger.info("Finished scanning the target file %s" % args.tfile)
		return

	# This is the default behavior of fetching work from the server
	else:
		while True:
			time.sleep(60)


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		global_logger.info("Shutting down due to keyboard interrupt")
