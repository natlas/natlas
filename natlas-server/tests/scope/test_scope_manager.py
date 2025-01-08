from datetime import datetime

from app import db, scope_manager
from app.models import RescanTask, ScopeItem, User
from app.scope import ScopeManager

network_lengths = {"/0": 4294967296, "/8": 16777216, "/16": 65536, "/24": 256, "/32": 1}


def test_new_scopemanager(app):  # type: ignore[no-untyped-def]
    sm = ScopeManager()
    sm.init_app(app)
    assert sm.get_scope() == []
    assert sm.get_blacklist() == []
    assert sm.scanmanager is None
    assert datetime.utcnow() > sm.init_time  # type: ignore[operator]


def test_scope_update(app):  # type: ignore[no-untyped-def]
    scope_items = ["10.0.0.0/8"]
    for s in scope_items:
        item = ScopeItem(target=s, blacklist=False)
        db.session.add(item)
    scope_manager.update()
    assert scope_manager.get_scope_size() == network_lengths["/8"]
    assert scope_manager.is_acceptable_target("10.1.2.3")


def test_blacklist_update(app):  # type: ignore[no-untyped-def]
    scope_items = ["10.0.0.0/8"]
    blacklist_items = ["10.10.10.0/24"]
    for s in scope_items:
        item = ScopeItem(target=s, blacklist=False)
        db.session.add(item)
    for s in blacklist_items:
        item = ScopeItem(target=s, blacklist=True)
        db.session.add(item)
    scope_manager.update()
    assert scope_manager.get_blacklist_size() == network_lengths["/24"]
    assert scope_manager.get_scope_size() == network_lengths["/8"]
    assert (
        scope_manager.get_effective_scope_size()
        == network_lengths["/8"] - network_lengths["/24"]
    )
    assert scope_manager.is_acceptable_target("10.10.11.1")
    assert not scope_manager.is_acceptable_target("10.10.10.10")


def test_acceptable_targets(app):  # type: ignore[no-untyped-def]
    scope_items = ["192.168.0.0/16"]
    blacklist_items = ["192.168.1.0/24", "192.168.2.1/32"]
    for s in scope_items:
        item = ScopeItem(target=s, blacklist=False)
        db.session.add(item)
    for s in blacklist_items:
        item = ScopeItem(target=s, blacklist=True)
        db.session.add(item)
    scope_manager.update()
    assert scope_manager.is_acceptable_target("192.168.0.123")
    assert scope_manager.is_acceptable_target("192.168.2.2")
    assert not scope_manager.is_acceptable_target("192.168.1.234")
    assert not scope_manager.is_acceptable_target("192.168.2.1")
    assert not scope_manager.is_acceptable_target("192.0.2.34")
    assert not scope_manager.is_acceptable_target("example.com")


def test_rescan_lifecycle(app):  # type: ignore[no-untyped-def]
    scope_items = ["192.168.0.0/16"]
    user = User(email="test@example.com")
    db.session.add(user)
    for s in scope_items:
        item = ScopeItem(target=s, blacklist=False)
        db.session.add(item)
    scope_manager.update()
    assert scope_manager.get_pending_rescans() == []
    assert scope_manager.get_dispatched_rescans() == []
    assert scope_manager.get_incomplete_scans() == []
    r = RescanTask(target="192.168.123.45", user_id=user.id)
    db.session.add(r)
    scope_manager.update_pending_rescans()
    assert len(scope_manager.get_pending_rescans()) == 1
    assert len(scope_manager.get_incomplete_scans()) == 1
    r.dispatchTask()
    db.session.add(r)
    scope_manager.update_pending_rescans()
    scope_manager.update_dispatched_rescans()
    assert len(scope_manager.get_pending_rescans()) == 0
    assert len(scope_manager.get_dispatched_rescans()) == 1
    assert len(scope_manager.get_incomplete_scans()) == 1
    r.completeTask("testscanid")
    db.session.add(r)
    scope_manager.update_pending_rescans()
    scope_manager.update_dispatched_rescans()
    assert len(scope_manager.get_pending_rescans()) == 0
    assert len(scope_manager.get_dispatched_rescans()) == 0
    assert len(scope_manager.get_incomplete_scans()) == 0
