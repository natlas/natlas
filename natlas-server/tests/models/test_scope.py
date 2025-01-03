from app import db
from app.models import ScopeItem


def test_new_scope(app):  # type: ignore[no-untyped-def]
    test_scope = ScopeItem(target="10.0.0.0/8", blacklist=False)
    assert not test_scope.blacklist
    assert test_scope.target == "10.0.0.0/8"


def test_ip6_scope(app):  # type: ignore[no-untyped-def]
    test_scope = ScopeItem(target="2001:db8::/32", blacklist=False)
    assert not test_scope.blacklist
    assert test_scope.target == "2001:db8::/32"


def test_add_tags(app):  # type: ignore[no-untyped-def]
    tags = ["test", "tag", "three"]
    test_scope = ScopeItem(target="127.0.0.1/8", blacklist=False)
    db.session.add(test_scope)
    ScopeItem.addTags(test_scope, tags)
    for tag in test_scope.tags:  # type: ignore[attr-defined]
        assert test_scope.is_tagged(tag)


def test_del_tags(app):  # type: ignore[no-untyped-def]
    tags = ["test", "tags", "three"]
    test_scope = ScopeItem(target="127.0.0.1/8", blacklist=False)
    db.session.add(test_scope)
    ScopeItem.addTags(test_scope, tags)
    assert len([t.name for t in test_scope.tags]) == 3  # type: ignore[attr-defined]
    test_scope.delTag(test_scope.tags[2])  # type: ignore[index]
    assert len([t.name for t in test_scope.tags]) == 2  # type: ignore[attr-defined]


def test_get_scope(app):  # type: ignore[no-untyped-def]
    test_scope1 = ScopeItem(target="127.0.0.1/8", blacklist=False)
    test_scope2 = ScopeItem(target="172.16.0.0/16", blacklist=True)
    db.session.add(test_scope1)
    db.session.add(test_scope2)
    assert len(ScopeItem.getScope()) == 1
    assert len(ScopeItem.getBlacklist()) == 1


scopefile = """
127.0.0.1,one,two,three
10.11.12.13,four
10.12.13.14,
10.13.14.15,one,two
10.12.13.14
notevenanip
2001:db8::/32
"""


def test_import_scope(app):  # type: ignore[no-untyped-def]
    result = ScopeItem.import_scope_list(scopefile.split(), False)
    assert len(result["fail"]) == 1
    assert result["exist"] == 1
    assert result["success"] == 5
    item = ScopeItem.query.filter_by(target="127.0.0.1/32").first()
    tags = [t.name for t in item.tags]
    assert len(tags) == 3
    assert "one" in tags
    assert "four" not in tags
    item = ScopeItem.query.filter_by(target="10.12.13.14/32").first()
    assert len(item.tags) == 0
