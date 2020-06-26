import ipaddress
import os
import shutil
from pathlib import Path

from natlas import logging
from config import Config

utillogger = logging.get_logger("Utilities")
conf = Config()


def validate_target(target, config):
    try:
        iptarget = ipaddress.ip_address(target)
        if iptarget.is_private and not config.scan_local:
            utillogger.error("We're not configured to scan local addresses!")
            return False
    except ipaddress.AddressValueError:
        utillogger.error(f"{target} is not a valid IP Address")
        return False
    return True


def get_conf_dir():
    return os.path.join(conf.data_dir, "conf")


def get_services_path():
    return os.path.join(get_conf_dir(), "natlas-services")


def get_scan_dir(scan_id):
    return os.path.join(conf.data_dir, "scans", f"natlas.{scan_id}")


def create_scan_dir(scan_id):
    Path(get_scan_dir(scan_id)).mkdir(parents=True, exist_ok=True)


def delete_files(scan_id):
    scan_dir = get_scan_dir(scan_id)
    if os.path.isdir(scan_dir):
        shutil.rmtree(scan_dir)


def save_files(scan_id):
    failroot = os.path.join(conf.data_dir, "scans", "failures")
    scan_dir = get_scan_dir(scan_id)
    Path(failroot).mkdir(parents=True, exist_ok=True)
    if os.path.isdir(scan_dir):
        src = scan_dir
        dst = failroot
        shutil.move(src, dst)


def cleanup_files(scan_id, failed=False, saveFails=False):
    utillogger.info(f"Cleaning up files for {scan_id}")
    if saveFails and failed:
        save_files(scan_id)
    else:
        delete_files(scan_id)
