import requests
import random
import hashlib
import time
import json

from requests.packages.urllib3.exceptions import InsecureRequestWarning

from natlas import logging

class NatlasNetworkServices:

	config = None
	netlogger = logging.get_logger("NetworkServices")

	api_endpoints = {"GETSERVICES": "/api/natlas-services", "GETWORK": "/api/getwork", "SUBMIT": "/api/submit"}

	def __init__(self, config):
		self.config = config

		if self.config.ignore_ssl_warn:
			requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

	def make_request(self, endpoint, reqType="GET", postData=None, contentType="application/json", statusCode=200):
		headers = {'user-agent': 'natlas-agent/{}'.format(self.config.NATLAS_VERSION)}
		if self.config.agent_id and self.config.auth_token:
			authheader = self.config.agent_id + ":" + self.config.auth_token
			headers['Authorization'] = 'Bearer {}'.format(authheader)
		try:
			if reqType == "GET":
				req = requests.get(self.config.server+endpoint, timeout=self.config.request_timeout, headers=headers, verify=(not self.config.ignore_ssl_warn))
				if req.status_code == 200:
					if 'message' in req.json():
						self.netlogger.info("[Server] " + req.json()['message'])
					return req
				if req.status_code == 403:
					if 'message' in req.json():
						self.netlogger.error("[Server] " + req.json()['message'])
					if 'retry' in req.json() and not req.json()['retry']:
						os._exit(403)
				if req.status_code == 400:
					if 'message' in req.json():
						self.netlogger.warn("[Server] " + req.json()['message'])
					return req
				if req.status_code != statusCode:
					self.netlogger.error("Expected %s, received %s" % (statusCode, req.status_code))
					if 'message' in req.json():
						self.netlogger.warn("[Server] " + req.json()['message'])
					return req
				if req.headers['content-type'] != contentType:
					self.netlogger.warn("Expected %s, received %s" % (contentType, req.headers['content-type']))
					return False
			elif reqType == "POST" and postData:
				req = requests.post(self.config.server+endpoint, json=postData, timeout=self.config.request_timeout, headers=headers, verify=(not self.config.ignore_ssl_warn))
				if req.status_code == 200:
					if 'message' in req.json():
						self.netlogger.info("[Server] " + req.json()['message'])
					return req
				if req.status_code == 403:
					if 'message' in req.json():
						self.netlogger.error("[Server] " + req.json()['message'])
					if 'retry' in req.json() and not req.json()['retry']:
						os._exit(403)
				if req.status_code == 400:
					if 'message' in req.json():
						self.netlogger.warn("[Server] " + req.json()['message'])
					return req
				if req.status_code != statusCode:
					self.netlogger.warn("Expected %s, received %s" % (statusCode, req.status_code))
					if 'message' in req.json():
						self.netlogger.warn("[Server] " + req.json()['message'])
					return req
		except requests.ConnectionError as e:
			self.netlogger.warn("Connection Error connecting to %s" % self.config.server)
			return False
		except requests.Timeout as e:
			self.netlogger.warn("Request timed out after %s seconds." % self.config.request_timeout)
			return False
		except ValueError as e:
			self.netlogger.error("Error: %s" % e)
			return False

		return req

	def backoff_request(self, giveup=False, *args, **kwargs):
		attempt = 0
		result = None
		while not result:
			result = self.make_request(*args, **kwargs)
			RETRY=False

			if result is False: # Retry if there are connection errors
				RETRY=True
			elif 'retry' in result.json() and result.json()['retry']: # Retry if the server tells us to
				RETRY=True
			elif 'retry' in result.json() and not result.json()['retry']: # Don't retry if the server tells us not to
				return result
			elif not 'retry' in result.json(): # No instructions on whether to retry or not, so don't
				return result

			if RETRY:
				attempt += 1
				if giveup and attempt == self.config.max_retries:
					self.netlogger.warn("Request to %s failed %s times. Giving up" % (self.config.server, self.config.max_retries))
					return False
				jitter = random.randint(0,1000) / 1000 # jitter to reduce chance of locking
				current_sleep = min(self.config.backoff_max, self.config.backoff_base * 2 ** attempt) + jitter
				self.netlogger.warn("Request to %s failed. Waiting %s seconds before retrying." % (self.config.server, current_sleep))
				time.sleep(current_sleep)
		return result

	def get_services_file(self):
		self.netlogger.info("Fetching natlas-services file from %s" % self.config.server)
		response = self.backoff_request(endpoint=self.api_endpoints["GETSERVICES"])
		if response:
			serviceData = response.json()
			if serviceData["id"] == "None":
				self.netlogger.error("%s doesn't have a service file for us" % self.config.server)
				return False
			if not hashlib.sha256(serviceData["services"].encode()).hexdigest() == serviceData["sha256"]:
				self.netlogger.error("hash provided by %s doesn't match locally computed hash of services" % self.config.server)
				return False
			with open("tmp/natlas-services", "w") as f:
				f.write(serviceData["services"])
			with open("tmp/natlas-services", "r") as f:
				if not hashlib.sha256(f.read().rstrip('\r\n').encode()).hexdigest() == serviceData["sha256"]:
					self.netlogger.error("hash of local file doesn't match hash provided by server")
					return False
		else:
			return False # return false if we were unable to get a response from the server
		return serviceData["sha256"] # return True if we got a response and everything checks out


	def get_work(self, target=None):
		if target:
			self.netlogger.info("Getting work config for %s from %s" % (target, self.config.server))
			get_work_endpoint=self.api_endpoints["GETWORK"]+"?target="+target
		else:
			self.netlogger.info("Getting work from %s" % (self.config.server))
			get_work_endpoint=self.api_endpoints["GETWORK"]

		response = self.backoff_request(endpoint=get_work_endpoint)
		if response:
			work = response.json()
		else:
			return False # failed to get work from server
		return work

	# Results is a ScanResult object
	def submit_results(self, results):
		if 'timed_out' in results.result and results.result['timed_out']:
			self.netlogger.info("Submitting scan timeout notice for %s" % results.result['ip'])
		elif 'is_up' in results.result and results.result['is_up'] and 'port_count' in results.result and results.result['port_count'] >= 0:
			self.netlogger.info("Submitting %s ports for %s" % (results.result['port_count'], results.result['ip']))
		elif not results.result['is_up']:
			self.netlogger.info("Submitting host down notice for %s" % (results.result['ip']))
		else:
			self.netlogger.info("Submitting results for %s" % results.result["ip"])

		response = self.backoff_request(giveup=True, endpoint=self.api_endpoints["SUBMIT"], reqType="POST", postData=json.dumps(results.result))
		return response