import ipaddress
from netaddr import IPNetwork, IPAddress
from app import db
from app.models.dict_serializable import DictSerializable

# Many to many table that ties tags and scopes together
scopetags = db.Table(
    "scopetags",
    db.Column("scope_id", db.Integer, db.ForeignKey("scope_item.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class ScopeItem(db.Model, DictSerializable):
    id = db.Column(db.Integer, primary_key=True)
    target = db.Column(db.String(128), index=True, unique=True)
    blacklist = db.Column(db.Boolean, index=True)
    tags = db.relationship(
        "Tag",
        secondary=scopetags,
        primaryjoin=(scopetags.c.scope_id == id),
        backref=db.backref("scope", lazy=True),
        lazy=True,
    )
    addr_family = db.Column(db.Integer)
    start_addr = db.Column(db.VARBINARY(16))
    stop_addr = db.Column(db.VARBINARY(16))

    def __init__(self, target: str, blacklist: bool):
        self.target = target
        self.blacklist = blacklist
        self.parse_network_range(target)

    def parse_network_range(self, network: str):
        net = IPNetwork(network)
        self.addr_family = net.version
        size = 4 if net.version == 4 else 16
        self.start_addr = net.first.to_bytes(size, byteorder="big")
        self.stop_addr = net.last.to_bytes(size, byteorder="big")

    @staticmethod
    def get_overlapping_ranges(addr: str) -> list:
        addr = IPAddress(addr)
        size = 4 if addr.version == 4 else 16
        binval = addr.value.to_bytes(size, byteorder="big")
        return (
            ScopeItem.query.filter(ScopeItem.addr_family == addr.version)
            .filter(ScopeItem.start_addr <= binval)
            .filter(ScopeItem.stop_addr >= binval)
            .all()
        )

    def addTag(self, tag):
        if not self.is_tagged(tag):
            self.tags.append(tag)

    def delTag(self, tag):
        if self.is_tagged(tag):
            self.tags.remove(tag)

    def is_tagged(self, tag):
        return tag in self.tags

    def get_tag_names(self):
        return [tag.name for tag in self.tags]

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
            if tag.strip() == "":  # If the tag is an empty string then don't use it
                continue
            tag_obj = Tag.create_if_none(tag)
            scopeitem.addTag(tag_obj)

    @staticmethod
    def parse_import_line(line):
        splitline = line.split(",")
        if len(splitline) > 1:
            ip = splitline[0]
            tags = splitline[1:]
        else:
            ip = line
            tags = []

        ip = ScopeItem.validate_ip(ip)
        return ip, tags

    @staticmethod
    def create_if_none(ip, blacklist, tags=[]):
        new = False
        item = ScopeItem.query.filter_by(target=ip).first()
        if not item:
            item = ScopeItem(target=ip, blacklist=blacklist)
            db.session.add(item)
            new = True
        if tags:
            ScopeItem.addTags(item, tags)
        return new, item

    @staticmethod
    def validate_ip(ip_str):
        try:
            # False will mask out hostbits for us, ip_network for eventual ipv6 compat
            return ipaddress.ip_network(ip_str, False)
        except ValueError:
            # if we hit this ValueError it means that the input couldn't be a CIDR range
            return False

    @staticmethod
    def import_scope_list(address_list, blacklist):
        fail, exists, success = [], [], []
        for line in address_list:
            ip, tags = ScopeItem.parse_import_line(line.strip())
            if not ip:
                fail.append(line)
                continue

            new, item = ScopeItem.create_if_none(ip.with_prefixlen, blacklist, tags)
            if not new:
                exists.append(item.target)
            else:
                success.append(item.target)

        return fail, exists, success
