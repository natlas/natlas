#!/usr/bin/env python3

import subprocess
import os
import time
import json
import base64
from urllib.parse import urlparse

from natlas import logging
from natlas import utils

logger = logging.get_logger("ScreenshotUtils")


def base64_image(path):
    img = None
    with open(path, "rb") as f:
        img = f.read()
    return str(base64.b64encode(img))[2:-1]


def get_web_screenshots(target, scan_id, xml_data, proctimeout):
    scan_dir = utils.get_scan_dir(scan_id)
    outFiles = os.path.join(scan_dir, f"aquatone.{scan_id}")
    output = []
    logger.info(f"Attempting to take screenshots for {target}")

    p1 = subprocess.Popen(["echo", xml_data], stdout=subprocess.PIPE)  # nosec
    aquatoneArgs = ["aquatone", "-nmap", "-scan-timeout", "2500", "-out", outFiles]
    process = subprocess.Popen(
        aquatoneArgs, stdin=p1.stdout, stdout=subprocess.DEVNULL
    )  # nosec
    p1.stdout.close()

    try:
        process.communicate(timeout=proctimeout)
        if process.returncode == 0:
            time.sleep(
                0.5
            )  # a small sleep to make sure all file handles are closed so that the agent can read them
    except subprocess.TimeoutExpired:
        logger.warning(f"TIMEOUT: Killing aquatone against {target}")
        process.kill()

    session_path = os.path.join(outFiles, "aquatone_session.json")
    if not os.path.isfile(session_path):
        return output

    with open(session_path) as f:
        session = json.load(f)

    if session["stats"]["screenshotSuccessful"] > 0:
        logger.info(
            f"{target} - Success: {session['stats']['screenshotSuccessful']}, Fail: {session['stats']['screenshotFailed']}"
        )

        for k, page in session["pages"].items():
            fqScreenshotPath = os.path.join(outFiles, page["screenshotPath"])
            if page["hasScreenshot"] and os.path.isfile(fqScreenshotPath):
                urlp = urlparse(page["url"])
                if not urlp.port and urlp.scheme == "http":
                    port = 80
                elif not urlp.port and urlp.scheme == "https":
                    port = 443
                else:
                    port = urlp.port
                logger.info(
                    f"{urlp.scheme.upper()} screenshot acquired for {page['hostname']} on port {port}"
                )
                output.append(
                    {
                        "host": page["hostname"],
                        "port": port,
                        "service": urlp.scheme.upper(),
                        "data": base64_image(fqScreenshotPath),
                    }
                )
    return output


def get_vnc_screenshots(target, scan_id, proctimeout):

    scan_dir = utils.get_scan_dir(scan_id)
    outFile = os.path.join(scan_dir, f"vncsnapshot.{scan_id}.jpg")

    logger.info(f"Attempting to take VNC screenshot for {target}")

    process = subprocess.Popen(
        ["xvfb-run", "vncsnapshot", "-quality", "50", target, outFile],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )  # nosec
    try:
        process.communicate(timeout=proctimeout)
        if process.returncode == 0:
            return True
    except Exception:
        try:
            logger.warning(f"TIMEOUT: Killing vncsnapshot against {target}")
            process.kill()
            return False
        except Exception:
            pass

    return False
