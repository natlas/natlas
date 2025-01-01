import pytest
from app.elastic import ElasticInterface
from tests.config import TestConfig

conf = TestConfig()


def reset_indices(indices):  # type: ignore[no-untyped-def]
    indices._delete_indices()
    indices._initialize_indices()


@pytest.fixture(scope="module")
def esinterface():  # type: ignore[no-untyped-def]
    esi = ElasticInterface(
        conf.ELASTICSEARCH_URL,
        True,
        "elastic",
        "natlas-dev-password-do-not-use",
        "natlas_test",
    )
    yield esi
    reset_indices(esi.indices)


@pytest.fixture(scope="module")
def esclient(esinterface):  # type: ignore[no-untyped-def]
    return esinterface.client
