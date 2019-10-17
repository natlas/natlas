import ipaddress
import string
import random
import os
import shutil
import glob

import natlaslogging



SCAN_ID_LENGTH = 16

utillogger = natlaslogging.get_logger("Utilities")


def validate_target(target, config):
	try:
		iptarget = ipaddress.ip_address(target)
		if iptarget.is_private and not config.scan_local:
			utillogger.error("We're not configured to scan local addresses!")
			return False
	except ipaddress.AddressValueError:
		utillogger.error("%s is not a valid IP Address" % target)
		return False
	return True

def generate_scan_id():
	return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(SCAN_ID_LENGTH))

def cleanup_files(scan_id):
	utillogger.info("Cleaning up files for %s" % scan_id)
	if os.path.isdir("data/aquatone.%s" % scan_id):
		shutil.rmtree("data/aquatone.%s" % scan_id)
	for file in glob.glob("data/natlas."+scan_id+".*"):
		try:
			os.remove(file)
		except Exception:
			utillogger.error("Could not remove file %s" % file)