from time import sleep


def test_delete_host(esinterface):
    ip = "127.0.0.1"
    esinterface.new_result({"ip": ip})
    esinterface.new_result({"ip": ip})
    sleep(1)
    assert esinterface.delete_host(ip) == 3


def test_delete_scan(esinterface):
    ip = "127.0.0.2"
    scan_id = "testscan"
    esinterface.new_result({"ip": ip, "scan_id": scan_id})
    esinterface.new_result({"ip": ip, "scan_id": scan_id * 2})
    sleep(1)
    assert esinterface.delete_scan(scan_id) == 1
    assert esinterface.delete_scan(scan_id * 2) == 2


def test_get_host(esinterface):
    ip = "127.0.0.3"
    esinterface.new_result({"ip": ip})
    sleep(1)
    count, host = esinterface.get_host(ip)
    assert count == 1
    assert ip == host["ip"]
    assert esinterface.delete_host(ip) == 2


def test_delete_scan_migrate(esinterface):
    ip = "127.0.0.4"
    scan_id = "testscan"
    scan_id2 = "nomatch"
    esinterface.new_result({"ip": ip, "scan_id": scan_id})
    esinterface.new_result({"ip": ip, "scan_id": scan_id2})
    sleep(1)
    assert esinterface.delete_scan(scan_id2) == 2
    sleep(1)
    count, host = esinterface.get_host(ip)
    assert count == 1
    assert host["ip"] == ip


def test_get_scan(esinterface):
    ip = "127.0.0.5"
    scan_id = "testscan1"
    esinterface.new_result({"ip": ip, "scan_id": scan_id})
    sleep(1)
    count, host = esinterface.get_host_by_scan_id(scan_id)
    assert count == 1
    assert ip == host["ip"] and scan_id == host["scan_id"]
    assert esinterface.delete_host(ip) == 2


def test_random_host(esinterface):
    ips = ["127.0.0.6", "127.0.0.7", "127.0.0.8"]
    for ip in ips:
        esinterface.new_result({"ip": ip, "port_count": 2, "is_up": True})
    sleep(1)
    assert esinterface.random_host()["ip"] in ips
    results = [esinterface.random_host()["ip"] for _ in range(5)]
    assert len(set(results)) > 1
