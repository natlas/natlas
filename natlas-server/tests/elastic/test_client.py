def test_ping(esclient):  # type: ignore[no-untyped-def]
    assert esclient._ping()
