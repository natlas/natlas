import requests
import random
import hashlib
import time
import json
import os

from requests.packages.urllib3.exceptions import InsecureRequestWarning

from natlas import logging
from natlas import utils


class NatlasNetworkServices:

    config = None
    netlogger = logging.get_logger("NetworkServices")

    api_endpoints = {
        "GETSERVICES": "/api/natlas-services",
        "GETWORK": "/api/getwork",
        "SUBMIT": "/api/submit",
    }

    def __init__(self, config):
        self.config = config

        if self.config.ignore_ssl_warn:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    def make_request(
        self,
        endpoint,
        reqType="GET",
        postData=None,
        contentType="application/json",
        statusCode=200,
    ):
        headers = {"user-agent": f"natlas-agent/{self.config.NATLAS_VERSION}"}
        if self.config.agent_id and self.config.auth_token:
            authheader = self.config.agent_id + ":" + self.config.auth_token
            headers["Authorization"] = f"Bearer {authheader}"
        args = {
            "timeout": self.config.request_timeout,
            "headers": headers,
            "verify": not self.config.ignore_ssl_warn,
        }
        try:
            if reqType == "GET":
                req = requests.get(self.config.server + endpoint, **args)
                if req.status_code == 200:
                    if "message" in req.json():
                        self.netlogger.info("[Server] " + req.json()["message"])
                    return req
                if req.status_code == 403:
                    if "message" in req.json():
                        self.netlogger.error("[Server] " + req.json()["message"])
                    if "retry" in req.json() and not req.json()["retry"]:
                        os._exit(403)
                if req.status_code == 400:
                    if "message" in req.json():
                        self.netlogger.warn("[Server] " + req.json()["message"])
                    return req
                if req.status_code != statusCode:
                    self.netlogger.error(
                        f"Expected {statusCode}, received {req.status_code}"
                    )
                    if "message" in req.json():
                        self.netlogger.warn("[Server] " + req.json()["message"])
                    return req
                if req.headers["content-type"] != contentType:
                    self.netlogger.warn(
                        "Expected %s, received %s"
                        % (contentType, req.headers["content-type"])
                    )
                    return False
            elif reqType == "POST" and postData:
                args["json"] = postData
                req = requests.post(self.config.server + endpoint, **args)
                if req.status_code == 200:
                    if "message" in req.json():
                        self.netlogger.info("[Server] " + req.json()["message"])
                    return req
                if req.status_code == 403:
                    if "message" in req.json():
                        self.netlogger.error("[Server] " + req.json()["message"])
                    if "retry" in req.json() and not req.json()["retry"]:
                        os._exit(403)
                if req.status_code == 400:
                    if "message" in req.json():
                        self.netlogger.warn("[Server] " + req.json()["message"])
                    return req
                if req.status_code != statusCode:
                    self.netlogger.warn(
                        f"Expected {statusCode}, received {req.status_code}"
                    )
                    if "message" in req.json():
                        self.netlogger.warn("[Server] " + req.json()["message"])
                    return req
        except requests.ConnectionError:
            self.netlogger.warn(f"Connection Error connecting to {self.config.server}")
            return False
        except requests.Timeout:
            self.netlogger.warn(
                f"Request timed out after {self.config.request_timeout} seconds."
            )
            return False
        except ValueError as e:
            self.netlogger.error(f"Error: {e}")
            return False

        return req

    def backoff_request(self, giveup=False, *args, **kwargs):
        attempt = 0
        result = None
        while not result:
            result = self.make_request(*args, **kwargs)
            RETRY = False

            if result is False:  # Retry if there are connection errors
                RETRY = True
            elif (
                "retry" in result.json() and result.json()["retry"]
            ):  # Retry if the server tells us to
                RETRY = True
            elif (
                "retry" in result.json() and not result.json()["retry"]
            ):  # Don't retry if the server tells us not to
                return result
            elif (
                "retry" not in result.json()
            ):  # No instructions on whether to retry or not, so don't
                return result

            if RETRY:
                attempt += 1
                if giveup and attempt == self.config.max_retries:
                    self.netlogger.warn(
                        "Request to %s failed %s times. Giving up"
                        % (self.config.server, self.config.max_retries)
                    )
                    return False
                jitter = (
                    random.randint(0, 1000) / 1000
                )  # jitter to reduce chance of locking
                current_sleep = (
                    min(
                        self.config.backoff_max, self.config.backoff_base * 2 ** attempt
                    )
                    + jitter
                )
                self.netlogger.warn(
                    "Request to %s failed. Waiting %s seconds before retrying."
                    % (self.config.server, current_sleep)
                )
                time.sleep(current_sleep)
        return result

    def get_services_file(self):
        self.netlogger.info(f"Fetching natlas-services file from {self.config.server}")
        services_path = utils.get_services_path()
        response = self.backoff_request(endpoint=self.api_endpoints["GETSERVICES"])
        if response:
            serviceData = response.json()
            if serviceData["id"] == "None":
                self.netlogger.error(
                    f"{self.config.server} doesn't have a service file for us"
                )
                return False
            if (
                hashlib.sha256(serviceData["services"].encode()).hexdigest()
                != serviceData["sha256"]
            ):
                self.netlogger.error(
                    "hash provided by %s doesn't match locally computed hash of services"
                    % self.config.server
                )
                return False
            with open(services_path, "w") as f:
                f.write(serviceData["services"])
            with open(services_path, "r") as f:
                if (
                    hashlib.sha256(f.read().rstrip("\r\n").encode()).hexdigest()
                    != serviceData["sha256"]
                ):
                    self.netlogger.error(
                        "hash of local file doesn't match hash provided by server"
                    )
                    return False
        else:
            return False  # return false if we were unable to get a response from the server
        return serviceData[
            "sha256"
        ]  # return True if we got a response and everything checks out

    def get_work(self, target=None):
        if target:
            self.netlogger.info(
                f"Getting work config for {target} from {self.config.server}"
            )
            get_work_endpoint = self.api_endpoints["GETWORK"] + "?target=" + target
        else:
            self.netlogger.info(f"Getting work from {self.config.server}")
            get_work_endpoint = self.api_endpoints["GETWORK"]

        response = self.backoff_request(endpoint=get_work_endpoint)
        if response:
            work = response.json()
        else:
            return False  # failed to get work from server
        return work

    # Results is a ScanResult object
    def submit_results(self, results):
        if "timed_out" in results.result and results.result["timed_out"]:
            self.netlogger.info(
                f"Submitting scan timeout notice for {results.result['ip']}"
            )
        elif (
            "is_up" in results.result
            and results.result["is_up"]
            and "port_count" in results.result
            and results.result["port_count"] >= 0
        ):
            self.netlogger.info(
                "Submitting %s ports for %s"
                % (results.result["port_count"], results.result["ip"])
            )
        elif not results.result["is_up"]:
            self.netlogger.info(
                f"Submitting host down notice for {results.result['ip']}"
            )
        else:
            self.netlogger.info(f"Submitting results for {results.result['ip']}")

        return self.backoff_request(
            giveup=True,
            endpoint=self.api_endpoints["SUBMIT"],
            reqType="POST",
            postData=json.dumps(results.result),
        )
