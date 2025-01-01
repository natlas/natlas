from app.scope.scan_manager import IPScanManager
from netaddr import IPSet


def test_new_scan_manager(app):
    scope = IPSet(["10.0.0.0/24"])
    blacklist = IPSet(["10.0.0.5/32"])
    mgr = IPScanManager(scope, blacklist, False)
    assert mgr.get_total() == 255
    assert mgr.get_ready()


def test_scan_cycle_complete_coverage(app):
    scope = IPSet(["10.0.0.0/24"])
    blacklist = IPSet()
    mgr = IPScanManager(scope, blacklist, False)
    result = [mgr.get_next_ip() for _ in range(mgr.get_total())]
    assert len(result) == len(set(result))
