#!/usr/bin/env python3

import base64
import json
import os
import subprocess
import time
from urllib.parse import urlparse

from PIL import Image, UnidentifiedImageError

from natlas import logging, utils

logger = logging.get_logger("ScreenshotUtils")


def base64_file(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def is_valid_image(path: str) -> bool:
    try:
        Image.open(path)
        return True
    except (FileNotFoundError, UnidentifiedImageError):
        return False


def parse_url(url: str) -> tuple:  # type: ignore[type-arg]
    urlp = urlparse(url)
    port = (80 if urlp.scheme == "http" else 443) if not urlp.port else urlp.port

    return urlp.scheme.upper(), port


def parse_aquatone_page(page: dict, file_path: str) -> dict:  # type: ignore[type-arg]
    if not (page["hasScreenshot"] and is_valid_image(file_path)):
        return {}
    scheme, port = parse_url(page["url"])
    logger.info(f"{scheme} screenshot acquired for {page['hostname']} on port {port}")
    return {
        "host": page["hostname"],
        "port": port,
        "service": scheme,
        "data": base64_file(file_path),
    }


def get_aquatone_session(base_dir: str) -> dict:  # type: ignore[type-arg]
    session_path = os.path.join(base_dir, "aquatone_session.json")
    if not os.path.isfile(session_path):
        return {}

    with open(session_path) as f:
        session = json.load(f)

    if session["stats"]["screenshotSuccessful"] == 0:
        return {}
    return session  # type: ignore[no-any-return]


def parse_aquatone_session(base_dir: str) -> list:  # type: ignore[type-arg]
    session = get_aquatone_session(base_dir)
    if not session:
        return []

    output = []
    for _, page in session["pages"].items():
        fqScreenshotPath = os.path.join(base_dir, page["screenshotPath"])
        parsed_page = parse_aquatone_page(page, fqScreenshotPath)
        if not parsed_page:
            continue
        output.append(parsed_page)

    return output


def get_web_screenshots(target, scan_id, proctimeout):  # type: ignore[no-untyped-def]
    scan_dir = utils.get_scan_dir(scan_id)
    xml_file = os.path.join(scan_dir, f"nmap.{scan_id}.xml")
    output_dir = os.path.join(scan_dir, f"aquatone.{scan_id}")
    logger.info(f"Attempting to take screenshots for {target}")

    aquatoneArgs = [
        "aquatone",
        "-nmap",
        "-scan-timeout",
        "2500",
        "-threads",
        "1",
        "-out",
        output_dir,
    ]
    with open(xml_file) as f:
        process = subprocess.Popen(aquatoneArgs, stdin=f, stdout=subprocess.DEVNULL)  # nosec

    try:
        process.communicate(timeout=proctimeout)
        if process.returncode == 0:
            time.sleep(
                0.5
            )  # a small sleep to make sure all file handles are closed so that the agent can read them
    except subprocess.TimeoutExpired:
        logger.warning(f"TIMEOUT: Killing aquatone against {target}")
        process.kill()

    return parse_aquatone_session(output_dir)


def get_vnc_screenshots(target, scan_id, proctimeout):  # type: ignore[no-untyped-def]
    scan_dir = utils.get_scan_dir(scan_id)
    output_file = os.path.join(scan_dir, f"vncsnapshot.{scan_id}.jpg")

    logger.info(f"Attempting to take VNC screenshot for {target}")

    vncsnapshot_args = [
        "xvfb-run",
        "vncsnapshot",
        "-quality",
        "50",
        target,
        output_file,
    ]

    process = subprocess.Popen(
        vncsnapshot_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )  # nosec
    try:
        process.communicate(timeout=proctimeout)
    except subprocess.TimeoutExpired:
        logger.warning(f"TIMEOUT: Killing vncsnapshot against {target}")
        process.kill()

    if not is_valid_image(output_file):
        return {}

    logger.info(f"VNC screenshot acquired for {target} on port 5900")
    return {
        "host": target,
        "port": 5900,
        "service": "VNC",
        "data": base64_file(output_file),
    }
