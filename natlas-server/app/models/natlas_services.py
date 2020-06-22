import hashlib

from app import db


# While generally I prefer to use a singular model name, each record here is going to be storing a set of services
# Each record in this table is a complete nmap-services db
class NatlasServices(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	sha256 = db.Column(db.String(64))
	services = db.Column(db.Text)

	def __init__(self, services):
		self.services = services
		self.sha256 = hashlib.sha256(self.services.encode()).hexdigest()

	def hash_equals(self, hash):
		return self.sha256 == hash

	def services_as_list(self):
		servlist = []
		idx = 1
		for line in self.services.splitlines():
			# any empty newlines will be skipped, or comment lines (for uploaded files)
			if line == '' or line.startswith('#'):
				continue

			# split on whitespace, store as tuple
			portnum = line.split()[1].split('/')[0]
			portproto = line.split()[1].split('/')[1]
			servlist.append((idx, portnum, portproto, line.split()[0]))
			idx += 1
		return servlist

	def as_dict(self):
		servdict = {c.name: getattr(self, c.name) for c in self.__table__.columns}
		servdict['as_list'] = self.services_as_list()
		return servdict
