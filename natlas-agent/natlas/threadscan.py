import base64
import subprocess
import threading
import shutil
import os

from libnmap.parser import NmapParser, NmapParserException

from natlas import screenshots
from natlas import logging
from natlas.net import NatlasNetworkServices
from natlas.scanresult import ScanResult
from natlas import utils


logger = logging.get_logger("AgentThread")

def command_builder(scan_id, agentConfig, target):
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


def scan(target_data, config):

	if not utils.validate_target(target_data["target"], config):
		return False

	target = target_data["target"]
	scan_id = target_data["scan_id"]

	agentConfig = target_data["agent_config"]

	command = command_builder(scan_id, agentConfig, target)

	result = ScanResult(target_data, config)

	try:
		process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=int(agentConfig["scanTimeout"])) # nosec
	except subprocess.TimeoutExpired:
		result.add_item('timed_out', True)
		logger.warn("TIMEOUT: Nmap against %s (%s)" % (target, scan_id))
		return result

	logger.info("Nmap %s (%s) complete" % (target, scan_id))

	for ext in 'nmap', 'gnmap', 'xml':
		try:
			result.add_item(ext+"_data", open("data/natlas."+scan_id+"."+ext).read())
		except Exception:
			logger.warn("Couldn't read natlas.%s.%s" % (scan_id, ext))
			return False

	try:
		nmap_report = NmapParser.parse(result.result['xml_data'])
	except NmapParserException:
		logger.warn("Couldn't parse natlas.%s.xml" % (scan_id))
		return False

	if nmap_report.hosts_total < 1:
		logger.warn("No hosts found in natlas.%s.xml" % (scan_id))
		return False
	elif nmap_report.hosts_total > 1:
		logger.warn("Too many hosts found in natlas.%s.xml" % (scan_id))
		return False
	elif nmap_report.hosts_down == 1:
		# host is down
		result.is_up(False)
		return result
	elif nmap_report.hosts_up == 1 and len(nmap_report.hosts) == 0:
		# host is up but no reportable ports were found
		result.is_up(True)
		result.add_item('port_count', 0)
		return result
	else:
		# host is up and reportable ports were found
		result.is_up(nmap_report.hosts[0].is_up())
		result.add_item('port_count', len(nmap_report.hosts[0].get_ports()))


	if agentConfig["webScreenshots"] and shutil.which("aquatone") is not None:
		targetServices=[]
		if "80/tcp" in result.result['nmap_data']:
			targetServices.append("http")
		if "443/tcp" in result.result['nmap_data']:
			targetServices.append("https")
		if len(targetServices) > 0:
			screenshots.get_web_screenshots(target, scan_id, targetServices)

		serviceMapping = {
			"http": 80,
			"https": 443
		}
		for service in targetServices:
			screenshotPath = "data/aquatone." + scan_id + "/screenshots/" + service + "__" + target.replace('.', '_') + ".png"

			if not os.path.isfile(screenshotPath):
				continue

			result.add_screenshot({
				"host": target,
				"port": serviceMapping[service],
				"service": service.upper(),
				"data": str(base64.b64encode(open(screenshotPath, 'rb').read()))[2:-1]
			})
			logger.info("%s screenshot acquired for %s" % (service.upper(), target))

	if agentConfig["vncScreenshots"] and shutil.which("vncsnapshot") is not None:
		if "5900/tcp" in result.result['nmap_data']:
			if screenshots.get_vnc_screenshots(target, scan_id) is True:
				result.add_screenshot({
					"host": target,
					"port": 5900,
					"service": "VNC",
					"data": str(base64.b64encode(open("data/natlas."+scan_id+".vnc.jpg", 'rb').read()))[2:-1]
				})
				logger.info("VNC screenshot acquired for %s" % result.result['ip'])

	# submit result

	return result


class ThreadScan(threading.Thread):
	def __init__(self, queue, config, auto=False, servicesSha=''):
		threading.Thread.__init__(self)
		self.queue = queue
		self.auto = auto
		self.servicesSha = servicesSha
		self.config = config
		self.netsrv = NatlasNetworkServices(self.config)

	def run(self):
		# If we're in auto mode, the threads handle getting work from the server
		if self.auto:
			while True:
				target_data = self.netsrv.get_work()
				# We hit this if we hit an error that we shouldn't recover from.
				# Primarily version mismatch, at this point.
				if not target_data:
					os._exit(400)
				if target_data and target_data["services_hash"] != self.servicesSha:
					self.servicesSha = self.netsrv.get_services_file()
					if not self.servicesSha:
						logger.warn("Failed to get updated services from %s" % config.server)
				result = scan(target_data, self.config)
				if not result:
					logger.warn("Not submitting data for %s" % target_data['target'])
					continue
				result.scan_stop()
				response = self.netsrv.submit_results(result)
				utils.cleanup_files(target_data['scan_id'])

		else:
			#If we're not in auto mode, then the queue is populated with work from local data
			while True:
				logger.info("Fetching work from queue")
				target_data = self.queue.get()
				if target_data is None:
					break
				logger.info("Manual Target: %s" % target_data["target"])
				result = scan(target_data, self.config)
				if not result:
					logger.warn("Not submitting data for %s" % target_data['target'])
					continue
				result.scan_stop()
				response = self.netsrv.submit_results(result)
				utils.cleanup_files(target_data['scan_id'])
				self.queue.task_done()