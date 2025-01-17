import pytest
from app.elastic import ElasticInterface
from app.elastic.client import ElasticClient
from app.elastic.indices import ElasticIndices
from flask import current_app


def reset_indices(indices: ElasticIndices) -> None:
    indices._delete_indices()
    indices._initialize_indices()


@pytest.fixture(scope="module")
def esinterface():  # type: ignore[no-untyped-def]
    esi = ElasticInterface()
    esi.init_app(current_app)
    yield esi
    reset_indices(esi.indices)


@pytest.fixture(scope="module")
def esclient(esinterface: ElasticInterface) -> ElasticClient:
    return esinterface.client
