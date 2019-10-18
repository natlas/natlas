#!/usr/bin/env python3

import subprocess
import os
import time

from natlas import logging
from natlas import utils

logger = logging.get_logger("ScreenshotUtils")

def get_web_screenshots(target, scan_id, services, proctimeout):
	data_dir = utils.get_data_dir(scan_id)
	outFiles = f"{data_dir}/aquatone.{scan_id}"
	inputstring = ""
	for service in services:
		inputstring += service + "://" + target + "\n"

	if inputstring:
		inputstring = inputstring[:-1] # trim trailing newline because otherwise chrome spits garbage into localhost for some reason

	logger.info("Attempting to take %s screenshot(s) for %s" % (', '.join(services).upper(),target))

	p1 = subprocess.Popen(["echo", inputstring], stdout=subprocess.PIPE) # nosec
	process = subprocess.Popen(["aquatone", "-scan-timeout", "2500", "-out", outFiles], stdin=p1.stdout, stdout=subprocess.DEVNULL) # nosec
	p1.stdout.close()

	try:
		out,err = process.communicate(timeout=proctimeout)
		if process.returncode is 0:
			time.sleep(0.5) # a small sleep to make sure all file handles are closed so that the agent can read them
			return True
	except subprocess.TimeoutExpired:
		logger.warning("TIMEOUT: Killing aquatone against %s" % target)
		process.kill()

	return False

def get_vnc_screenshots(target, scan_id, proctimeout):
	if "DISPLAY" not in os.environ:
		return False

	data_dir = utils.get_data_dir(scan_id)
	outFile = f"{data_dir}/vncsnapshot.{scan_id}.jpg"

	logger.info("Attempting to take VNC screenshot for %s" % target)

	process = subprocess.Popen(["xvfb-run", "vncsnapshot", "-quality", "50", target, outFile], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) # nosec
	try:
		out, err = process.communicate(timeout=proctimeout)
		if process.returncode is 0:
			return True
	except Exception:
		try:
			logger.warning("TIMEOUT: Killing vncsnapshot against %s" % target)
			process.kill()
			return False
		except Exception:
			pass

	return False
