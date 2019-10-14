import ipaddress
from datetime import datetime, timezone
import random

def hostinfo(ip):
	from flask import current_app, abort
	hostinfo = {}
	count, context = current_app.elastic.gethost(ip)
	if count == 0:
		return abort(404)
	hostinfo['history'] = count
	screenshot_count = current_app.elastic.count_host_screenshots(ip)
	hostinfo['screenshot_count'] = screenshot_count
	screenshots = 0
	screenshotTypes = ['screenshots', 'headshot', 'vncheadshot',
					 'httpheadshot', 'httpsheadshot']
	for hs in screenshotTypes:
		if context.get(hs):
			if hs == "screenshots": # 0.6.5 iterating screenshots instead of screenshot types
				for item in context.get(hs):
					screenshots += 1
			else:
				screenshots += 1
	hostinfo['screenshots'] = screenshots
	if context.get('hostname'):
		hostinfo['hostname'] = context.get('hostname')
	return hostinfo, context

def isAcceptableTarget(target):
	from flask import current_app, abort
	targetAddr = ipaddress.IPv4Address(target)
	inScope = False
	# if zero, update to make sure that the scopemanager has been populated
	if current_app.ScopeManager.getScopeSize() == 0:
		current_app.ScopeManager.update()
	for network in current_app.ScopeManager.getScope():
		if str(network).endswith('/32'):
			if targetAddr == ipaddress.IPv4Address(str(network).split('/32')[0]):
				inScope = True
		if targetAddr in network:
			inScope = True

	if not inScope:
		return False

	for network in current_app.ScopeManager.getBlacklist():
		if str(network).endswith('/32'):
			if targetAddr == ipaddress.IPv4Address(str(network).split('/32')[0]):
				return False
		if targetAddr in network:
			return False

	return True

def utcnow_tz():
	return datetime.now(timezone.utc)

def generate_hex_16():
	return "%x" % random.randrange(16**16)

def generate_hex_32():
	return "%x" % random.randrange(16**32)

def parse_ssl_data(sslcert):
	altnames = []
	# Parse out Subject Alternative Names because libnmap doesn't give them to us
	for line in sslcert['output'].split('\n'):
		if line.startswith("Subject Alternative Name:"):
			for item in line.split(' ')[3:]:
				altnames.append(item.strip(',').split('DNS:')[1])

	elements = sslcert['elements']

	result = {
		"subject": {
			"commonName": elements['subject']['commonName'],
			"altNames": altnames
		},
		"issuer": elements['issuer'],
		"pubkey": {
			"type": elements['pubkey']["type"],
			"bits": int(elements['pubkey']["bits"])
		},
		"sig_alg": elements['sig_algo'],
		"notAfter": elements['validity']['notAfter'],
		"notBefore": elements['validity']['notBefore'],
		"md5": elements["md5"],
		"sha1": elements['sha1'],
		"pem": elements['pem']
	}
	return result