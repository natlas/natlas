from flask import current_app
import base64
import hashlib
from PIL import Image
import random
from ipaddress import ip_network
import string
import os
from app.models import ScopeItem


def get_target_tags(target):
	targetnet = ip_network(target)
	tags = []
	for scope in current_app.ScopeManager.getScope():
		if scope.overlaps(targetnet):
			scopetags = ScopeItem.query.filter_by(target=str(scope)).first().tags.all()
			for tag in scopetags:
				tags.append(tag.name)
	return list(set(tags)) # make it a set for only uniques, then make it a list to serialize to JSON


def get_unique_scan_id():
	scan_id = ''
	while scan_id == '':
		rand = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(16))
		count, context = current_app.elastic.gethost_scan_id(rand)
		if count == 0:
			scan_id = rand
	return scan_id


def prepare_work(work):
	work['tags'] = get_target_tags(work['target'])
	work['type'] = 'nmap'
	work['agent_config'] = current_app.agentConfig
	work['agent_config']['scripts'] = current_app.agentScriptStr
	work["services_hash"] = current_app.current_services["sha256"]
	work['scan_id'] = get_unique_scan_id()
	work['status'] = 200
	work['message'] = "Target: " + str(work['target'])
	return work


def parse_alt_names(cert_data):
	altnames = []
	# Parse out Subject Alternative Names because libnmap doesn't give them to us
	for line in cert_data.split('\n'):
		if line.startswith("Subject Alternative Name:"):
			for item in line.split(' ')[3:]:
				altname = item.strip(',').split('DNS:')
				if len(altname) > 1: # Prevent an indexerror in edge case
					altnames.append(altname[1])
	return altnames


def parse_subject(subject, altnames):
	subDict = {}
	if subject.get('commonName'):
		subDict['commonName'] = subject.get('commonName')
	if altnames:
		subDict['altNames'] = altnames
	return subDict


def parse_pubkey(pubkey):
	pubkeyDict = {}
	if pubkey.get('type'):
		pubkeyDict['type'] = pubkey.get('type')
	if pubkey.get('bits'):
		pubkeyDict['bits'] = int(pubkey.get('bits'))
	return pubkeyDict


def parse_ssl_data(sslcert):
	altnames = parse_alt_names(sslcert['output'])
	elements = sslcert['elements']
	subject = elements.get('subject')
	issuer = elements.get('issuer')
	pubkey = elements.get('pubkey')
	sig_alg = elements.get('sig_algo')
	validity = elements.get('validity')
	md5 = elements.get('md5')
	sha1 = elements.get('sha1')
	pem = elements.get('pem')

	result = {}
	if subject:
		result['subject'] = parse_subject(subject, altnames)

	if issuer:
		result['issuer'] = issuer

	if pubkey:
		result['pubkey'] = parse_pubkey(pubkey)

	if sig_alg:
		result['sig_alg'] = sig_alg

	if validity:
		if validity.get('notAfter'):
			result['notAfter'] = validity.get('notAfter')
		if validity.get('notBefore'):
			result['notBefore'] = validity.get('notBefore')
	if md5:
		result['md5'] = md5
	if sha1:
		result['sha1'] = sha1
	if pem:
		result['pem'] = pem

	return result


def create_thumbnail(fname, file_ext):
	thumb_size = (255, 160)
	thumb = Image.open(fname)
	thumb.thumbnail(thumb_size)
	thumb_hash = hashlib.sha256(thumb.tobytes()).hexdigest()
	thumbhashpath = "{}/{}".format(thumb_hash[0:2], thumb_hash[2:4])
	thumbpath = os.path.join(current_app.config["MEDIA_DIRECTORY"], "thumbs", thumbhashpath)
	# makedirs attempts to make every directory necessary to get to the "thumbs" folder
	os.makedirs(thumbpath, exist_ok=True)
	fname = os.path.join(thumbpath, thumb_hash + file_ext)
	thumb.save(fname)
	thumb.close()
	return thumb_hash


def process_screenshots(screenshots):
	# Handle screenshots

	num_screenshots = 0
	for item in screenshots:
		if item['service'] == 'VNC':
			file_ext = '.jpg'
		else: # Handles http, https files from aquatone/chromium-headless
			file_ext = '.png'

		image = base64.b64decode(item['data'])
		image_hash = hashlib.sha256(image).hexdigest()

		hashpath = "{}/{}".format(image_hash[0:2], image_hash[2:4])
		dirpath = os.path.join(current_app.config["MEDIA_DIRECTORY"], "original", hashpath)

		# makedirs attempts to make every directory necessary to get to the "original" folder
		os.makedirs(dirpath, exist_ok=True)

		fname = os.path.join(dirpath, image_hash + file_ext)
		with open(fname, 'wb') as f:
			f.write(image)
		item['hash'] = image_hash
		del item['data']

		item['thumb_hash'] = create_thumbnail(fname, file_ext)
		num_screenshots += 1

	return screenshots, num_screenshots
