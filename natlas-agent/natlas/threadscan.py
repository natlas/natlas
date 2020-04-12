import base64
import subprocess
import threading
import shutil
import os

from libnmap.parser import NmapParser, NmapParserException
from sentry_sdk import capture_exception

from natlas import screenshots
from natlas import logging
from natlas.net import NatlasNetworkServices
from natlas.scanresult import ScanResult
from natlas import utils


logger = logging.get_logger("AgentThread")


def command_builder(scan_id, agentConfig, target):
	outFiles = utils.get_data_dir(scan_id) + f"/nmap.{scan_id}"
	command = ["nmap", "--privileged", "-oA", outFiles, "--servicedb", "./tmp/natlas-services"]

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

	for k, v in agentConfig.items():
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
	data_dir = utils.get_data_dir(scan_id)

	result = ScanResult(target_data, config)

	try:
		subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=int(agentConfig["scanTimeout"])) # nosec
	except subprocess.TimeoutExpired:
		result.add_item('timed_out', True)
		logger.warning("TIMEOUT: Nmap against %s (%s)" % (target, scan_id))
		return result

	logger.info("Nmap %s (%s) complete" % (target, scan_id))

	for ext in 'nmap', 'gnmap', 'xml':
		path = f"{data_dir}/nmap.{scan_id}.{ext}"
		try:
			result.add_item(ext + "_data", open(path).read())
		except Exception:
			logger.warning(f"Couldn't read {path}")
			return False

	try:
		nmap_report = NmapParser.parse(result.result['xml_data'])
	except NmapParserException:
		logger.warning(f"Couldn't parse nmap.{scan_id}.xml")
		return False

	if nmap_report.hosts_total < 1:
		logger.warning(f"No hosts found in nmap.{scan_id}.xml")
		return False
	elif nmap_report.hosts_total > 1:
		logger.warning(f"Too many hosts found in nmap.{scan_id}.xml")
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
		screens = screenshots.get_web_screenshots(target, scan_id, result.result['xml_data'], agentConfig["webScreenshotTimeout"])
		for item in screens:
			result.add_screenshot(item)

	if agentConfig["vncScreenshots"] and shutil.which("vncsnapshot") is not None:
		if "5900/tcp" in result.result['nmap_data']:
			if screenshots.get_vnc_screenshots(target, scan_id, agentConfig["vncScreenshotTimeout"]) is True:

				screenshotPath = f"{data_dir}/vncsnapshot.{scan_id}.jpg"
				if os.path.isfile(screenshotPath):
					result.add_screenshot({
						"host": target,
						"port": 5900,
						"service": "VNC",
						"data": str(base64.b64encode(open(screenshotPath, 'rb').read()))[2:-1]
					})
					logger.info("VNC screenshot acquired for %s" % result.result['ip'])

	# submit result

	return result


class ScanWorkItem:
	def __init__(self, target_data):
		self.target_data = target_data

	def complete(self):
		pass


class ManualScanWorkItem(ScanWorkItem):
	def __init__(self, queue, target_data):
		super(ManualScanWorkItem, self).__init__(target_data)
		self.queue = queue

	def complete(self):
		super()
		self.queue.task_done()


class ThreadScan(threading.Thread):
	def __init__(self, queue, config, auto=False, servicesSha=''):
		threading.Thread.__init__(self)
		self.queue = queue
		self.auto = auto
		self.servicesSha = servicesSha
		self.config = config
		self.netsrv = NatlasNetworkServices(self.config)

	def execute_scan(self, work_item):
		target_data = work_item.target_data
		utils.create_data_dir(target_data['scan_id'])
		# setting this here ensures the finally block won't error if we don't submit data
		response = False
		try:
			result = scan(target_data, self.config)

			if not result:
				logger.warning("Not submitting data for %s" % target_data['target'])
				return
			result.scan_stop()
			response = self.netsrv.submit_results(result)
		finally:
			didFail = response is False
			utils.cleanup_files(target_data['scan_id'], failed=didFail, saveFails=self.config.save_fails)

	def run(self):
		try:
			while True:
				work_item = self.get_work()

				if not work_item:
					break

				self.execute_scan(work_item)
				work_item.complete()
		except Exception as e:
			logger.warning("Failed to process work item: %s" % e)
			capture_exception(e)

	def get_work(self):
		# If we're in auto mode, the threads handle getting work from the server
		if self.auto:
			target_data = self.netsrv.get_work()
			# We hit this if we hit an error that we shouldn't recover from.
			# Primarily version mismatch, at this point.
			if not target_data:
				return None
			if target_data["services_hash"] != self.servicesSha:
				self.servicesSha = self.netsrv.get_services_file()
				if not self.servicesSha:
					logger.warning("Failed to get updated services from %s" % self.config.server)

			return ScanWorkItem(target_data)
		else: # Manual
			target_data = self.queue.get()
			if not target_data:
				return None

			logger.info("Manual Target: %s" % target_data["target"])
			return ManualScanWorkItem(self.queue, target_data)
