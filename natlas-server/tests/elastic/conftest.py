import pytest

from app.elastic import ElasticInterface
from tests.config import TestConfig

conf = TestConfig()


def reset_indices(indices):
    indices._delete_indices()
    indices._initialize_indices()


@pytest.fixture(scope="module")
def esinterface():
    esi = ElasticInterface(conf.ELASTICSEARCH_URL, "natlas_test")
    yield esi
    reset_indices(esi.indices)


@pytest.fixture(scope="module")
def esclient(esinterface):
    return esinterface.client
