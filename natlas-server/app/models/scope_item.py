from app import db
import ipaddress
from app.models.dict_serializable import DictSerializable


# Many to many table that ties tags and scopes together
scopetags = db.Table(
	'scopetags',
	db.Column('scope_id', db.Integer, db.ForeignKey('scope_item.id'), primary_key=True),
	db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)


class ScopeItem(db.Model, DictSerializable):
	id = db.Column(db.Integer, primary_key=True)
	target = db.Column(db.String, index=True, unique=True)
	blacklist = db.Column(db.Boolean, index=True)
	tags = db.relationship(
		'Tag',
		secondary=scopetags,
		primaryjoin=(scopetags.c.scope_id == id),
		backref=db.backref('scope', lazy='dynamic'),
		lazy='dynamic')

	def addTag(self, tag):
		if not self.is_tagged(tag):
			self.tags.append(tag)

	def delTag(self, tag):
		if self.is_tagged(tag):
			self.tags.remove(tag)

	def is_tagged(self, tag):
		return self.tags.filter(scopetags.c.tag_id == tag.id).count() > 0

	@staticmethod
	def getBlacklist():
		return ScopeItem.query.filter_by(blacklist=True).all()

	@staticmethod
	def getScope():
		return ScopeItem.query.filter_by(blacklist=False).all()

	@staticmethod
	def addTags(scopeitem, tags):
		from app.models import Tag
		for tag in tags:
			if tag.strip() == '': # If the tag is an empty string then don't use it
				continue
			tag_obj = Tag.create_if_none(tag)
			scopeitem.addTag(tag_obj)

	@staticmethod
	def parse_import_line(line):
		splitline = line.split(',')
		if len(splitline) > 1:
			ip = splitline[0]
			tags = splitline[1:]
		else:
			ip = line
			tags = []

		if '/' not in ip:
			ip = ip + '/32'

		return ip, tags

	@staticmethod
	def create_if_none(ip, blacklist):
		new = False
		item = ScopeItem.query.filter_by(target=ip).first()
		if not item:
			item = ScopeItem(target=ip, blacklist=blacklist)
			db.session.add(item)
			new = True
		return new, item

	@staticmethod
	def importScope(line, blacklist):
		failedImports = []
		alreadyExists = []
		successImports = []
		ip, tags = ScopeItem.parse_import_line(line)

		try:
			# False will mask out hostbits for us, ip_network for eventual ipv6 compat
			isValid = ipaddress.ip_network(ip, False)
		except ValueError:
			# if we hit this ValueError it means that the input couldn't be a CIDR range
			failedImports.append(line)
			return failedImports, alreadyExists, successImports

		new, item = ScopeItem.create_if_none(isValid.with_prefixlen, blacklist)
		if tags:
			ScopeItem.addTags(item, tags)
		if not new:
			alreadyExists.append(item.target)
			return failedImports, alreadyExists, successImports
		else:
			successImports.append(item.target)

		return failedImports, alreadyExists, successImports
