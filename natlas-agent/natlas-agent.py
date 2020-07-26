#!/usr/bin/env python3

import subprocess
import time
import os
import argparse
import hashlib
import ipaddress
import queue
from pathlib import Path

from natlas import logging, error_reporting, utils
from config import Config
from natlas.threadscan import ThreadScan
from natlas.net import NatlasNetworkServices

ERR = {"INVALIDTARGET": 1, "SCANTIMEOUT": 2, "DATANOTFOUND": 3, "INVALIDDATA": 4}

config = Config()
MAX_QUEUE_SIZE = (
    config.max_threads
)  # only queue enough work for each of our active threads

global_logger = logging.get_logger("MainThread")
netsrv = NatlasNetworkServices(config)


def add_targets_to_queue(target, q):
    targetNetwork = ipaddress.ip_network(target.strip())
    if targetNetwork.num_addresses == 1:
        target_data = netsrv.get_work(target=str(targetNetwork.network_address))
        if not target_data:
            return
        q.put(target_data)
    else:
        # Iterate over usable hosts in target, queue.put will block until a queue slot is available
        for t in targetNetwork.hosts():
            target_data = netsrv.get_work(target=str(t))
            if not target_data:
                continue
            q.put(target_data)


def main():

    PARSER_DESC = "Scan hosts and report data to a configured server. The server will reject your findings if they are deemed not in scope."
    PARSER_EPILOG = "Report problems to https://github.com/natlas/natlas"
    parser = argparse.ArgumentParser(
        description=PARSER_DESC, epilog=PARSER_EPILOG, prog="natlas-agent"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {config.NATLAS_VERSION}"
    )
    mutually_exclusive = parser.add_mutually_exclusive_group()
    mutually_exclusive.add_argument(
        "--target",
        metavar="IPADDR",
        help="An IP address or CIDR range to scan. e.g. 192.168.0.1, 192.168.0.1/24, 2001:db8:dead:dade:fade:cafe:babe:beef/128",
        dest="target",
    )
    mutually_exclusive.add_argument(
        "--target-file",
        metavar="FILENAME",
        help="A file of line separated target IP addresses or CIDR ranges",
        dest="tfile",
    )
    args = parser.parse_args()

    # Check if Nmap has required capabilities to run as a non-root user
    try:
        nmap_path = (
            subprocess.check_output(["which", "nmap"]).decode("utf-8").strip()
        )  # nosec
        nmap_caps = subprocess.check_output(["getcap", nmap_path]).decode(
            "utf-8"
        )  # nosec
    except subprocess.CalledProcessError:
        msg = "Couldn't find nmap"
        global_logger.critical(msg)
        raise SystemExit(f"[!] {msg}")

    needed_caps = ["cap_net_raw", "cap_net_admin", "cap_net_bind_service"]
    missing_caps = [cap for cap in needed_caps if cap not in nmap_caps]
    if missing_caps:
        msg = f"Missing Nmap capabilities: {' '.join(missing_caps)}"
        global_logger.critical(msg)
        raise SystemExit(f"[!] {msg}")

    required_dirs = ["scans", "logs", "conf"]
    for directory in required_dirs:
        req_dir = os.path.join(config.data_dir, directory)
        Path(req_dir).mkdir(parents=True, exist_ok=True)

    autoScan = True
    if args.target or args.tfile:
        autoScan = False

    # Initialize SentryIo after basic environment checks complete
    error_reporting.initialize_sentryio(config)
    q = queue.Queue(maxsize=MAX_QUEUE_SIZE)

    servicesSha = ""
    SERVICESPATH = utils.get_services_path()
    if os.path.isfile(SERVICESPATH):
        with open(SERVICESPATH, "r") as f:
            servicesSha = hashlib.sha256(f.read().rstrip("\r\n").encode()).hexdigest()
    else:
        servicesSha = netsrv.get_services_file()
        if not servicesSha:
            raise SystemExit(
                f"[!] Failed to get valid services file from {config.server}"
            )

    # Start threads that will wait for items in queue and then scan them
    for i in range(config.max_threads):
        # Stagger thread init in batches of 10 to more evenly distribute startup load
        if i and not i % 10:
            time.sleep(5)
        t = ThreadScan(q, config, autoScan, servicesSha)
        t.setDaemon(True)
        t.start()

    if args.target:
        global_logger.info(f"Scanning: {args.target}")
        add_targets_to_queue(args.target, q)
        q.join()
        global_logger.info(f"Finished scanning: {args.target}")
        return

    elif args.tfile:
        global_logger.info(f"Reading scope from file: {args.tfile}")
        with open(args.tfile, "r") as f:
            for target in f:
                add_targets_to_queue(target, q)
        q.join()
        global_logger.info(f"Finished scanning the target file {args.tfile}")
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
