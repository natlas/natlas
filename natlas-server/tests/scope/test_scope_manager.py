from datetime import datetime

from flask import current_app
from netaddr import IPSet

from app.scope import ScopeManager
from app import db
from app.models import ScopeItem, RescanTask, User

network_lengths = {"/0": 4294967296, "/8": 16777216, "/16": 65536, "/24": 256, "/32": 1}


def test_new_scopemanager(app):
    sm = ScopeManager()
    assert sm.scope == []
    assert sm.blacklist == []
    assert sm.scope_set == IPSet()
    assert sm.blacklist_set == IPSet()
    assert sm.scanmanager is None
    assert datetime.utcnow() > sm.init_time


def test_scope_update(app):
    scope_items = ["10.0.0.0/8"]
    for s in scope_items:
        item = ScopeItem(target=s, blacklist=False)
        db.session.add(item)
    current_app.ScopeManager.update()
    assert current_app.ScopeManager.get_scope_size() == network_lengths["/8"]
    assert current_app.ScopeManager.is_acceptable_target("10.1.2.3")


def test_blacklist_update(app):
    scope_items = ["10.0.0.0/8"]
    blacklist_items = ["10.10.10.0/24"]
    for s in scope_items:
        item = ScopeItem(target=s, blacklist=False)
        db.session.add(item)
    for s in blacklist_items:
        item = ScopeItem(target=s, blacklist=True)
        db.session.add(item)
    current_app.ScopeManager.update()
    assert current_app.ScopeManager.get_blacklist_size() == network_lengths["/24"]
    assert current_app.ScopeManager.get_scope_size() == network_lengths["/8"]
    assert (
        current_app.ScopeManager.get_effective_scope_size()
        == network_lengths["/8"] - network_lengths["/24"]
    )
    assert current_app.ScopeManager.is_acceptable_target("10.10.11.1")
    assert not current_app.ScopeManager.is_acceptable_target("10.10.10.10")


def test_acceptable_targets(app):
    scope_items = ["192.168.0.0/16"]
    blacklist_items = ["192.168.1.0/24", "192.168.2.1/32"]
    for s in scope_items:
        item = ScopeItem(target=s, blacklist=False)
        db.session.add(item)
    for s in blacklist_items:
        item = ScopeItem(target=s, blacklist=True)
        db.session.add(item)
    current_app.ScopeManager.update()
    assert current_app.ScopeManager.is_acceptable_target("192.168.0.123")
    assert current_app.ScopeManager.is_acceptable_target("192.168.2.2")
    assert not current_app.ScopeManager.is_acceptable_target("192.168.1.234")
    assert not current_app.ScopeManager.is_acceptable_target("192.168.2.1")
    assert not current_app.ScopeManager.is_acceptable_target("192.0.2.34")
    assert not current_app.ScopeManager.is_acceptable_target("example.com")


def test_rescan_lifecycle(app):
    scope_items = ["192.168.0.0/16"]
    user = User(email="test@example.com")
    db.session.add(user)
    for s in scope_items:
        item = ScopeItem(target=s, blacklist=False)
        db.session.add(item)
    current_app.ScopeManager.update()
    assert current_app.ScopeManager.get_pending_rescans() == []
    assert current_app.ScopeManager.get_dispatched_rescans() == []
    assert current_app.ScopeManager.get_incomplete_scans() == []
    r = RescanTask(target="192.168.123.45", user_id=user.id)
    db.session.add(r)
    current_app.ScopeManager.update_pending_rescans()
    assert len(current_app.ScopeManager.get_pending_rescans()) == 1
    assert len(current_app.ScopeManager.get_incomplete_scans()) == 1
    r.dispatchTask()
    db.session.add(r)
    current_app.ScopeManager.update_pending_rescans()
    current_app.ScopeManager.update_dispatched_rescans()
    assert len(current_app.ScopeManager.get_pending_rescans()) == 0
    assert len(current_app.ScopeManager.get_dispatched_rescans()) == 1
    assert len(current_app.ScopeManager.get_incomplete_scans()) == 1
    r.completeTask("testscanid")
    db.session.add(r)
    current_app.ScopeManager.update_pending_rescans()
    current_app.ScopeManager.update_dispatched_rescans()
    assert len(current_app.ScopeManager.get_pending_rescans()) == 0
    assert len(current_app.ScopeManager.get_dispatched_rescans()) == 0
    assert len(current_app.ScopeManager.get_incomplete_scans()) == 0
