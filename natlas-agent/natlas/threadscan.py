import ipaddress
import os
import queue
import subprocess
import threading
from typing import Any, Literal

from config import Config
from libnmap.parser import NmapParser, NmapParserException
from sentry_sdk import add_breadcrumb, capture_exception, push_scope

from natlas import logging, screenshots, utils
from natlas.net import NatlasNetworkServices
from natlas.scan_work import ManualScanWorkItem, ScanWorkItem
from natlas.scanresult import ScanResult

logger = logging.get_logger("AgentThread")
conf = Config()


def command_builder(
    scan_id: str, agentConfig: dict[str, Any], target: str
) -> list[str]:
    outFiles = os.path.join(utils.get_scan_dir(scan_id), f"nmap.{scan_id}")
    servicepath = utils.get_services_path()
    command = ["nmap", "--privileged", "-oA", outFiles, "--servicedb", servicepath]

    commandDict = {
        "versionDetection": "-sV",
        "osDetection": "-O",
        "osScanLimit": "--osscan-limit",
        "noPing": "-Pn",
        "onlyOpens": "--open",
        "udpScan": "-sUS",
        "enableScripts": "--script={scripts}",
        "scriptTimeout": "--script-timeout={scriptTimeout}",
        "hostTimeout": "--host-timeout={hostTimeout}",
    }

    for k, _v in agentConfig.items():
        if agentConfig[k] and k in commandDict:
            command.append(commandDict[k].format(**agentConfig))
    if ipaddress.ip_network(target).version == 6:
        command.append("-6")
    command.append(target)
    return command


def scan(target_data: dict[str, Any], config: Config) -> ScanResult | Literal[False]:
    if not utils.validate_target(target_data["target"], config):
        return False
    target = target_data["target"]
    scan_id = target_data["scan_id"]

    agentConfig = target_data["agent_config"]

    command = command_builder(scan_id, agentConfig, target)
    scan_dir = utils.get_scan_dir(scan_id)

    result = ScanResult(target_data, config)

    try:
        subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=int(agentConfig["scanTimeout"]),
            check=False,
        )  # nosec
    except subprocess.TimeoutExpired:
        add_breadcrumb(level="warn", message="Nmap scan timed out")
        result.add_item("timed_out", True)
        logger.warning(f"TIMEOUT: Nmap against {target} ({scan_id})")
        return result
    logger.info(f"Nmap {target} ({scan_id}) complete")

    for ext in "nmap", "gnmap", "xml":
        path = os.path.join(scan_dir, f"nmap.{scan_id}.{ext}")
        try:
            with open(path) as f:
                result.add_item(ext + "_data", f.read())
        except Exception:
            logger.warning(f"Couldn't read {path}")
            return False
    try:
        nmap_report = NmapParser.parse(result.result["xml_data"])
    except NmapParserException:
        logger.warning(f"Couldn't parse nmap.{scan_id}.xml")
        return False
    if nmap_report.hosts_total < 1:
        logger.warning(f"No hosts found in nmap.{scan_id}.xml")
        return False
    if nmap_report.hosts_total > 1:
        logger.warning(f"Too many hosts found in nmap.{scan_id}.xml")
        return False
    if nmap_report.hosts_down == 1:
        # host is down
        result.is_up(False)
        return result
    if nmap_report.hosts_up == 1 and len(nmap_report.hosts) == 0:
        # host is up but no reportable ports were found
        result.is_up(True)
        result.add_item("port_count", 0)
        return result
    # host is up and reportable ports were found
    result.is_up(nmap_report.hosts[0].is_up())
    result.add_item("port_count", len(nmap_report.hosts[0].get_ports()))
    if agentConfig["webScreenshots"]:
        screens = screenshots.get_web_screenshots(
            target, scan_id, agentConfig["webScreenshotTimeout"]
        )
        for item in screens:
            result.add_screenshot(item)
    if agentConfig["vncScreenshots"] and "5900/tcp" in result.result["nmap_data"]:
        vnc_screenshot = screenshots.get_vnc_screenshots(
            target, scan_id, agentConfig["vncScreenshotTimeout"]
        )
        if vnc_screenshot:
            result.add_screenshot(vnc_screenshot)
    # submit result

    return result


class ThreadScan(threading.Thread):
    def __init__(
        self,
        queue: queue.Queue[dict[str, Any]],
        config: Config,
        auto: bool = False,
        servicesSha: str = "",
    ) -> None:
        threading.Thread.__init__(self)
        self.queue = queue
        self.auto = auto
        self.servicesSha = servicesSha
        self.config = config
        self.netsrv = NatlasNetworkServices(self.config)

    def execute_scan(self, work_item: ScanWorkItem) -> None:
        target_data = work_item.target_data
        utils.create_scan_dir(target_data["scan_id"])
        # setting this here ensures the finally block won't error if we don't submit data
        response = False
        try:
            result = scan(target_data, self.config)

            if not result:
                logger.warning(f"Not submitting data for {target_data['target']}")
                return
            result.scan_stop()
            response = self.netsrv.submit_results(result)
        finally:
            didFail = response is False
            utils.cleanup_files(
                target_data["scan_id"], failed=didFail, saveFails=self.config.save_fails
            )

    def run(self) -> None:
        while True:
            with push_scope() as scope:
                add_breadcrumb(
                    category="scan_workflow", message="Fetching work", level="info"
                )
                work_item = self.get_work()

                if work_item is None:
                    break
                scope.set_extra("natlas_scan_id", work_item.target_data["scan_id"])
                add_breadcrumb(
                    category="scan_workflow",
                    message=f"Starting scan for {work_item.target_data['target']}",
                    level="info",
                )
                try:
                    self.execute_scan(work_item)
                    add_breadcrumb(
                        category="scan_workflow",
                        message="Scan completed. Reporting",
                        level="info",
                    )
                    work_item.complete()
                except Exception as e:
                    event_id = capture_exception(e)
                    logger.warning(
                        f"Failed to process work item: {e}. Sentry event id: {event_id}"
                    )

    def get_work(self) -> ScanWorkItem | ManualScanWorkItem | None:
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
                    logger.warning(
                        f"Failed to get updated services from {self.config.server}"
                    )
            return ScanWorkItem(target_data)
        # Manual
        manual_target = self.queue.get()
        logger.info(f"Manual Target: {manual_target['target']}")
        return ManualScanWorkItem(self.queue, manual_target)
