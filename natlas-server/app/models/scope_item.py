from collections.abc import Iterable

from netaddr import IPAddress, IPNetwork
from netaddr.core import AddrFormatError

from app import db
from app.models.dict_serializable import DictSerializable
from app.models.tag import Tag

# Many to many table that ties tags and scopes together
scopetags = db.Table(
    "scopetags",
    db.Column("scope_id", db.Integer, db.ForeignKey("scope_item.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)


class ScopeItem(db.Model, DictSerializable):  # type: ignore[misc, name-defined]
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

    def parse_network_range(self, network: str):  # type: ignore[no-untyped-def]
        net = IPNetwork(network)
        self.addr_family = net.version
        size = 4 if net.version == 4 else 16
        self.start_addr = net.first.to_bytes(size, byteorder="big")
        self.stop_addr = net.last.to_bytes(size, byteorder="big")

    @staticmethod
    def get_overlapping_ranges(addr: str) -> list:  # type: ignore[type-arg]
        addr = IPAddress(addr)
        size = 4 if addr.version == 4 else 16  # type: ignore[attr-defined]
        binval = addr.value.to_bytes(size, byteorder="big")  # type: ignore[attr-defined]
        return (  # type: ignore[no-any-return]
            ScopeItem.query.filter(ScopeItem.addr_family == addr.version)  # type: ignore[attr-defined]
            .filter(ScopeItem.start_addr <= binval)
            .filter(ScopeItem.stop_addr >= binval)
            .all()
        )

    def addTag(self, tag: Tag):  # type: ignore[no-untyped-def]
        if not self.is_tagged(tag):
            self.tags.append(tag)

    def delTag(self, tag: Tag):  # type: ignore[no-untyped-def]
        if self.is_tagged(tag):
            self.tags.remove(tag)

    def is_tagged(self, tag: Tag):  # type: ignore[no-untyped-def]
        return tag in self.tags  # type: ignore[attr-defined]

    def get_tag_names(self):  # type: ignore[no-untyped-def]
        return [tag.name for tag in self.tags]  # type: ignore[attr-defined]

    @staticmethod
    def getBlacklist():  # type: ignore[no-untyped-def]
        return ScopeItem.query.filter_by(blacklist=True).all()

    @staticmethod
    def getScope():  # type: ignore[no-untyped-def]
        return ScopeItem.query.filter_by(blacklist=False).all()

    @staticmethod
    def addTags(scopeitem, tags: Iterable):  # type: ignore[no-untyped-def, type-arg]
        from app.models import Tag

        for tag in tags:
            if tag.strip() == "":  # If the tag is an empty string then don't use it
                continue
            tag_obj = Tag.create_if_none(tag)
            scopeitem.addTag(tag_obj)

    @staticmethod
    def parse_tags(tags: Iterable) -> Iterable:  # type: ignore[type-arg]
        return [t for t in tags if t.strip() != ""]

    @staticmethod
    def parse_import_line(line: str):  # type: ignore[no-untyped-def]
        splitline = line.split(",")
        tags = []  # type: ignore[var-annotated]
        if len(splitline) > 1:
            ip = splitline[0]
            tags = ScopeItem.parse_tags(splitline[1:])  # type: ignore[assignment]
        else:
            ip = line
        ip = ScopeItem.validate_ip(ip)
        return ip, tags

    @staticmethod
    def extract_import_tags(import_list: list) -> Iterable[str]:  # type: ignore[type-arg]
        out = set()  # type: ignore[var-annotated]
        for line in import_list:
            split = line.split(",")
            if len(split) > 1:
                tags = ScopeItem.parse_tags(split[1:])
                out.update(tags)
        return out

    @staticmethod
    def create_if_none(ip: str, blacklist: bool, tags=None):  # type: ignore[no-untyped-def]
        if tags is None:
            tags = []
        new = False
        item = ScopeItem.query.filter_by(target=ip).first()
        if not item:
            item = ScopeItem(target=ip, blacklist=blacklist)
            new = True
        for tag in tags:
            item.addTag(tag)
        return new, item

    @staticmethod
    def validate_ip(ip: str):  # type: ignore[no-untyped-def]
        try:
            return IPNetwork(ip)
        except AddrFormatError:
            return False

    @staticmethod
    def import_scope_list(address_list: Iterable, blacklist: bool) -> dict:  # type: ignore[type-arg]
        result = {"fail": [], "success": 0, "exist": 0}
        prefixes = {"sqlite": " OR IGNORE", "mysql": " IGNORE"}
        selected_prefix = prefixes.get(db.engine.dialect.name)
        scope_import = {}
        scope_tag_import = {}
        address_list = [line.strip() for line in address_list]
        tags = ScopeItem.extract_import_tags(address_list)
        from app.models import Tag

        tag_dict = {tag: Tag.create_if_none(tag) for tag in tags}
        db.session.commit()
        for line in address_list:
            ip, tags = ScopeItem.parse_import_line(line)
            if not ip:
                result["fail"].append(line)  # type: ignore[attr-defined]
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
        result["exist"] = len(address_list) - len(result["fail"]) - result["success"]  # type: ignore[arg-type, operator]
        all_scope = {item.target: item.id for item in ScopeItem.query.all()}
        tags_to_import = []  # type: ignore[var-annotated]
        for k, v in scope_tag_import.items():
            tags_to_import.extend(
                {"scope_id": all_scope[k], "tag_id": tag.id}  # type: ignore[attr-defined]
                for tag in v
            )
        import_chunks = [
            tags_to_import[i : i + chunk_size]
            for i in range(0, len(tags_to_import), chunk_size)
        ]
        for chunk in import_chunks:
            tag_stmt = scopetags.insert().prefix_with(selected_prefix).values(chunk)  # type: ignore[arg-type]
            db.session.execute(tag_stmt)
        db.session.commit()
        return result
