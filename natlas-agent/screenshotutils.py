#!/usr/bin/env python3

import subprocess
import os
import time

import natlaslogging

logger = natlaslogging.getLogger("ScreenshotUtils")

def runAquatone(target, scan_id, services):
	inputstring = ""
	for service in services:
		inputstring += service + "://" + target + "\n"

	if inputstring:
		inputstring = inputstring[:-1] # trim trailing newline because otherwise chrome spits garbage into localhost for some reason

	logger.info("Attempting to take %s screenshot(s) for %s" % (', '.join(services).upper(),target))

	p1 = subprocess.Popen(["echo", inputstring], stdout=subprocess.PIPE)
	process = subprocess.Popen(["aquatone", "-scan-timeout", "1000", "-out", "data/aquatone."+scan_id], stdin=p1.stdout, stdout=subprocess.DEVNULL)
	p1.stdout.close()

	try:
		out,err = process.communicate(timeout=60)
		if process.returncode is 0:
			time.sleep(0.5) # a small sleep to make sure all file handles are closed so that the agent can read them
			return True
	except subprocess.TimeoutExpired:
		logger.warn("TIMEOUT: Killing aquatone against %s" % target)
		process.kill()

	return False

def runVNCSnapshot(target, scan_id):
	if "DISPLAY" not in os.environ:
		return False

	logger.info("Attempting to take VNC screenshot for %s" % target)

	process = subprocess.Popen(["xvfb-run", "vncsnapshot", "-quality", "50", target, "data/natlas." +
								scan_id + ".vnc.jpg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	try:
		out, err = process.communicate(timeout=60)
		if process.returncode is 0:
			return True
	except Exception:
		try:
			logger.warn("TIMEOUT: Killing vncsnapshot against %s" % target)
			process.kill()
			return False
		except Exception:
			pass

	return False
