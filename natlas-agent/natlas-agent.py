#!/usr/bin/env python3

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


# my wrapper for screenshotting servers
import screenshotutils
import natlaslogging
from natlasnet import NatlasNetworkServices
import natlasutils
from scanresult import ScanResult
from config import Config

ERR = {"INVALIDTARGET":1,"SCANTIMEOUT":2, "DATANOTFOUND":3, "INVALIDDATA": 4}

config = Config()
MAX_QUEUE_SIZE = int(config.max_threads) # only queue enough work for each of our active threads

RTTVAR_MSG = "RTTVAR has grown to over"


global_logger = natlaslogging.getLogger("natlas-agent")

netsrv = NatlasNetworkServices(config)


def commandBuilder(scan_id, agentConfig, target):
	command = ["nmap", "--privileged", "-oA", "data/natlas."+scan_id, "--servicedb", "./natlas-services"]

	commandDict = {
		"versionDetection": "-sV",
		"osDetection": "-O",
		"osScanLimit": "--osscan-limit",
		"noPing": "-Pn",
		"onlyOpens": "--open",
		"udpScan": "-sUS",
		"enableScripts": "--script={scripts}",
		"scriptTimeout": "--script-timeout={scriptTimeout}",
		"hostTimeout": "--host-timeout={hostTimeout}"
	}

	for k,v in agentConfig.items():
		if agentConfig[k] and k in commandDict:
			command.append(commandDict[k].format(**agentConfig))

	command.append(target)

	return command



def scan(target_data=None):

	if not natlasutils.validate_target(target_data["target"], config):
		return False

	target = target_data["target"]
	scan_id = target_data["scan_id"]

	agentConfig = target_data["agent_config"]

	command = commandBuilder(scan_id, agentConfig, target)

	result = ScanResult(target_data, config)

	TIMEDOUT = False
	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
	try:
		out, err = process.communicate(timeout=int(agentConfig["scanTimeout"]))
	except Exception:
		try:
			TIMEDOUT = True
			global_logger.error("Scan %s timed out" % scan_id)
			process.kill()
		except Exception:
			pass

	if TIMEDOUT:
		result.addItem('timed_out', True)
		global_logger.info("Submitting scan timeout notice for %s" % result.result['ip'])
		return result
	else:
		global_logger.info("Scan %s Complete" % scan_id)

	for ext in 'nmap', 'gnmap', 'xml':
		try:
			result.addItem(ext+"_data", open("data/natlas."+scan_id+"."+ext).read())
		except Exception:
			global_logger.error("Couldn't read natlas.%s.%s" % (scan_id, ext))
			return False

	try:
		nmap_report = NmapParser.parse(result.result['xml_data'])
	except NmapParserException:
		global_logger.error("Couldn't parse natlas.%s.xml" % (scan_id))
		return False

	if nmap_report.hosts_total < 1:
		global_logger.error("No hosts found in scan data")
		return False
	elif nmap_report.hosts_total > 1:
		global_logger.error("Too many hosts found in scan data")
		return False
	elif nmap_report.hosts_down == 1:
		# host is down
		result.isUp(False)
		global_logger.info("Submitting host down notice for %s" % (result.result['ip']))
		return result
	elif nmap_report.hosts_up == 1 and len(nmap_report.hosts) == 0:
		# host is up but no reportable ports were found
		result.isUp(True)
		result.addItem('port_count', 0)
		global_logger.info("Submitting %s ports for %s" % (result.result['port_count'], result.result['ip']))
		return result
	else:
		# host is up and reportable ports were found
		result.isUp(nmap_report.hosts[0].is_up())
		result.addItem('port_count', len(nmap_report.hosts[0].get_ports()))


	if agentConfig["webScreenshots"] and shutil.which("aquatone") is not None:
		targetServices=[]
		if "80/tcp" in result.result['nmap_data']:
			targetServices.append("http")
		if "443/tcp" in result.result['nmap_data']:
			targetServices.append("https")
		if len(targetServices) > 0:
			global_logger.info("Attempting to take %s screenshot(s) for %s" % (', '.join(targetServices).upper(),result.result['ip']))
			screenshotutils.runAquatone(target, scan_id, targetServices)

		serviceMapping = {
			"http": 80,
			"https": 443
		}
		for service in targetServices:
			screenshotPath = "data/aquatone." + scan_id + "/screenshots/" + service + "__" + target.replace('.', '_') + ".png"

			if not os.path.isfile(screenshotPath):
				continue

			result.addScreenshot({
				"host": target,
				"port": serviceMapping[service],
				"service": service.upper(),
				"data": str(base64.b64encode(open(screenshotPath, 'rb').read()))[2:-1]
			})
			global_logger.info("%s screenshot acquired for %s" % (service.upper(), target))

	if agentConfig["vncScreenshots"] and shutil.which("vncsnapshot") is not None:
		if "5900/tcp" in result.result['nmap_data']:
			global_logger.info("Attempting to take VNC screenshot for %s" % result.result['ip'])
			if screenshotutils.runVNCSnapshot(target, scan_id) is True:
				result.addScreenshot({
					"host": target,
					"port": 5900,
					"service": "VNC",
					"data": str(base64.b64encode(open("data/natlas."+scan_id+".vnc.jpg", 'rb').read()))[2:-1]
				})
				global_logger.info("VNC screenshot acquired for %s" % result.result['ip'])
			else:
				global_logger.error("Failed to acquire screenshot for %s" % result.result['ip'])

	# submit result
	global_logger.info("Submitting %s ports for %s" % (result.result['port_count'], result.result['ip']))
	return result

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
				target_data = netsrv.get_work()
				# We hit this if we hit an error that we shouldn't recover from.
				# Primarily version mismatch, at this point.
				if not target_data:
					os._exit(400)
				if target_data and target_data["services_hash"] != self.servicesSha:
					self.servicesSha = netsrv.get_services_file()
					if not self.servicesSha:
						global_logger.error("Failed to get updated services from %s" % config.server)
				result = scan(target_data)
				result.scanStop()
				response = netsrv.submit_results(result)
				natlasutils.cleanup_files(target_data['scan_id'])

		else:
			#If we're not in auto mode, then the queue is populated with work from local data
			while True:
				global_logger.info("Fetching work from queue")
				target_data = self.queue.get()
				if target_data is None:
					break
				global_logger.info("Manual Target: %s" % target_data["target"])
				result = scan(target_data)
				result.scanStop()
				response = netsrv.submit_results(result)
				natlasutils.cleanup_files(target_data['scan_id'])
				self.queue.task_done()

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
	nmap_caps = subprocess.check_output(["getcap", "/usr/bin/nmap"]).decode("utf-8")

	needed_caps = ["cap_net_raw", "cap_net_admin", "cap_net_bind_service"]
	missing_caps = [cap for cap in needed_caps if cap not in nmap_caps]
	if missing_caps:
		raise SystemExit("[!] Missing Nmap capabilities: %s" % " ".join(missing_caps))

	if not os.path.isdir("data"):
		os.mkdir("data")
	if not os.path.isdir("logs"):
		os.mkdir("logs")

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
		servicesSha = netsrv.get_services_file()
		if not servicesSha:
			raise SystemExit("[!] Failed to get valid services file from %s" % config.server)

	# Start threads that will wait for items in queue and then scan them
	for i in range(int(config.max_threads)):
		t = ThreadScan(q, autoScan, servicesSha)
		t.setDaemon(True)
		t.start()

	# Use a default agent config of all options enabled if we are in standalone mode
	defaultAgentConfig = {
		"id": 0,
		"versionDetection": True,
		"osDetection": True,
		"enableScripts": True,
		"onlyOpens": True,
		"scanTimeout": 660,
		"webScreenshots": True,
		"vncScreenshots": True,
		"scriptTimeout": 60,
		"hostTimeout": 600,
		"osScanLimit": True,
		"noPing": False,
		"udpScan": False,
		"scripts": "default"
	}
	target_data_template = {"agent_config": defaultAgentConfig, "scan_reason":"manual", "tags":[]}
	if args.target:
		global_logger.info("Scanning: %s" % args.target)

		targetNetwork = ipaddress.ip_interface(args.target)
		if targetNetwork.with_prefixlen.endswith('/32'):
			target_data = target_data_template.copy()
			target_data["target"] = str(targetNetwork.ip)
			target_data["scan_id"] = natlasutils.generate_scan_id()
			q.put(target_data)
		else:
			# Iterate over usable hosts in target, queue.put will block until a queue slot is available
			for t in targetNetwork.network.hosts():
				target_data = target_data_template.copy()
				target_data["target"] = str(t)
				target_data["scan_id"] = natlasutils.generate_scan_id()
				q.put(target_data)

		q.join()
		global_logger.info("Finished scanning: %s" % args.target)
		return

	elif args.tfile:
		global_logger.info("Reading scope from file: %s" % args.tfile)

		for target in open(args.tfile, "r"):
			targetNetwork = ipaddress.ip_interface(target.strip())
			if targetNetwork.with_prefixlen.endswith('/32'):
				target_data = target_data_template.copy()
				target_data["target"] = str(targetNetwork.ip)
				target_data["scan_id"] = natlasutils.generate_scan_id()
				q.put(target_data)
			else:
				for t in targetNetwork.network.hosts():
					target_data = target_data_template.copy()
					target_data["target"] = str(t)
					target_data["scan_id"] = natlasutils.generate_scan_id()
					q.put(target_data)
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
