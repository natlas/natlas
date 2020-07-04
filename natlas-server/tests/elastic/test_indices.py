from app.elastic.indices import ElasticIndices


def test_index_lifecycle(esclient):
    base = "unittest"
    new_indices = ElasticIndices(esclient, base)
    assert new_indices.name("latest") == base
    assert new_indices.name("history") == base + "_history"
    index_names = new_indices.all_indices()
    assert len(index_names) == 2
    for index in index_names:
        assert esclient.index_exists(index)
    new_indices._delete_indices()
    for index in index_names:
        assert not esclient.index_exists(index)
