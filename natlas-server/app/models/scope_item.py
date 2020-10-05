from netaddr import IPNetwork, IPAddress
from netaddr.core import AddrFormatError
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
    def extract_import_tags(import_list: list) -> set[str]:
        tags = set()
        for line in import_list:
            split = line.split(",")
            if len(split) > 1:
                for tag in split[1:]:
                    if tag.strip() == "":
                        continue
                    tags.add(tag)
        return tags

    @staticmethod
    def create_if_none(ip, blacklist, tags=[]):
        new = False
        item = ScopeItem.query.filter_by(target=ip).first()
        if not item:
            item = ScopeItem(target=ip, blacklist=blacklist)
            new = True
        for tag in tags:
            item.addTag(tag)
        return new, item

    @staticmethod
    def validate_ip(ip_str):
        try:
            return IPNetwork(ip_str)
        except AddrFormatError:
            return False

    @staticmethod
    def import_scope_list(address_list, blacklist) -> dict:
        result = {"fail": [], "success": 0, "exist": 0}
        prefixes = {"sqlite": " OR IGNORE", "mysql": " IGNORE"}
        selected_prefix = prefixes.get(db.session.bind.dialect.name)
        scope_import = {}
        scope_tag_import = {}
        address_list = [line.strip() for line in address_list]
        tags = ScopeItem.extract_import_tags(address_list)
        tag_dict = {}
        from app.models import Tag

        for tag in tags:
            tag_dict[tag] = Tag.create_if_none(tag)
        db.session.commit()
        for line in address_list:
            ip, tags = ScopeItem.parse_import_line(line)
            if not ip:
                result["fail"].append(line)
                continue
            tags = [tag_dict[tag] for tag in tags]
            item = ScopeItem(target=str(ip), blacklist=blacklist).as_dict()
            scope_tag_import[item["target"]] = tags
            scope_import[item["target"]] = item
        import_list = [v for _, v in scope_import.items()]
        chunk_size = 10000
        import_chunks = [
            import_list[i : i + chunk_size]
            for i in range(0, len(import_list), chunk_size)
        ]
        for chunk in import_chunks:
            ins_stmt = (
                ScopeItem.__table__.insert().prefix_with(selected_prefix).values(chunk)
            )
            ins_result = db.session.execute(ins_stmt)
            result["success"] += ins_result.rowcount
        result["exist"] = len(address_list) - len(result["fail"]) - result["success"]
        all_scope = {item.target: item.id for item in ScopeItem.query.all()}
        tags_to_import = []
        for k, v in scope_tag_import.items():
            for tag in v:
                tags_to_import.append(dict(scope_id=all_scope[k], tag_id=tag.id))
        import_chunks = [
            tags_to_import[i : i + chunk_size]
            for i in range(0, len(tags_to_import), chunk_size)
        ]
        for chunk in import_chunks:
            tag_stmt = scopetags.insert().prefix_with(selected_prefix).values(chunk)
            db.session.execute(tag_stmt)
        db.session.commit()
        return result
