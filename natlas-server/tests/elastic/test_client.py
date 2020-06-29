from app.elastic import ElasticClient

from config import Config


def test_ping():
    client = ElasticClient(Config().ELASTICSEARCH_URL)
    assert client._ping()
