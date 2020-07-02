from time import sleep


def test_delete_by_query(esinterface):
    esinterface.new_result({"ip": "127.0.0.1"})
    sleep(2)
    assert esinterface.delete_host("127.0.0.1") == 2
