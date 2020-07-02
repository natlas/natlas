import pytest

from app.elastic import ElasticInterface
from tests.config import TestConfig

test_indices = {"latest": "test", "history": "test_history"}


def reset_indices(esclient):
    for index in esclient.natlasIndices:
        esclient.es.indices.delete(index)
    esclient._initialize_indices()


@pytest.fixture(scope="module")
def esinterface():
    esi = ElasticInterface(TestConfig().ELASTICSEARCH_URL, test_indices)
    yield esi
    reset_indices(esi.client)


@pytest.fixture(scope="module")
def esclient(esinterface):
    return esinterface.client
