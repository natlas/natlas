from app import db
import ipaddress


# Many to many table that ties tags and scopes together
scopetags = db.Table(
	'scopetags',
	db.Column('scope_id', db.Integer, db.ForeignKey('scope_item.id'), primary_key=True),
	db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)


class ScopeItem(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	target = db.Column(db.String, index=True, unique=True)
	blacklist = db.Column(db.Boolean, index=True)
	tags = db.relationship(
		'Tag',
		secondary=scopetags,
		primaryjoin=(scopetags.c.scope_id == id),
		backref=db.backref('scope', lazy='dynamic'),
		lazy='dynamic')

	@staticmethod
	def getBlacklist():
		return ScopeItem.query.filter_by(blacklist=True).all()

	@staticmethod
	def getScope():
		return ScopeItem.query.filter_by(blacklist=False).all()

	def addTag(self, tag):
		if not self.is_tagged(tag):
			self.tags.append(tag)

	def delTag(self, tag):
		if self.is_tagged(tag):
			self.tags.remove(tag)

	def is_tagged(self, tag):
		return self.tags.filter(scopetags.c.tag_id == tag.id).count() > 0

	@staticmethod
	def addTags(scopeitem, tags):
		from app.models import Tag
		for tag in tags:
			if tag.strip() == '': # If the tag is an empty string then don't use it
				continue
			existingTag = Tag.query.filter_by(name=tag).first()
			if existingTag:
				scopeitem.addTag(existingTag)
			else:
				newTag = Tag(name=tag.strip())
				db.session.add(newTag)
				scopeitem.addTag(newTag)

	@staticmethod
	def importScope(line, blacklist):
		failedImports = []
		alreadyExists = []
		successImports = []
		if len(line.split(',')) > 1:
			ip = line.split(',')[0]
			tags = line.split(',')[1:]
		else:
			ip = line
			tags = []

		if '/' not in ip:
			ip = ip + '/32'
		try:
			# False will mask out hostbits for us, ip_network for eventual ipv6 compat
			isValid = ipaddress.ip_network(ip, False)
		except ValueError:
			# if we hit this ValueError it means that the input couldn't be a CIDR range
			failedImports.append(line)
			return failedImports, alreadyExists, successImports
		# We only want scope items with masked out host bits
		item = ScopeItem.query.filter_by(target=isValid.with_prefixlen).first()
		if item:
			# Add in look for tags and append as necessary
			if tags:
				ScopeItem.addTags(item, tags)
			alreadyExists.append(isValid.with_prefixlen)
			return failedImports, alreadyExists, successImports
		else:
			newTarget = ScopeItem(target=isValid.with_prefixlen, blacklist=blacklist)
			db.session.add(newTarget)
			if tags:
				ScopeItem.addTags(newTarget, tags)
			successImports.append(isValid.with_prefixlen)

		return failedImports, alreadyExists, successImports

	def as_dict(self):
		return {c.name: getattr(self, c.name) for c in self.__table__.columns}
