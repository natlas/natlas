import ipaddress
import os
import shutil

from natlas import logging


utillogger = logging.get_logger("Utilities")


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


def create_data_dir(scan_id):
	data_folder = f"data/natlas.{scan_id}"
	os.makedirs(data_folder, exist_ok=True)


def get_data_dir(scan_id):
	data_folder = f"data/natlas.{scan_id}"
	return data_folder


def delete_files(scan_id):
	data_folder = f"data/natlas.{scan_id}"
	if os.path.isdir(data_folder):
		shutil.rmtree(data_folder)


def save_files(scan_id):
	failroot = "data/failures"
	if not os.path.isdir(failroot):
		os.mkdir(failroot)
	if os.path.isdir(f"data/natlas.{scan_id}"):
		src = f"data/natlas.{scan_id}"
		dst = f"data/failures/"
		shutil.move(src, dst)


def cleanup_files(scan_id, failed=False, saveFails=False):
	utillogger.info("Cleaning up files for %s" % scan_id)
	if saveFails and failed:
		save_files(scan_id)
	else:
		delete_files(scan_id)
