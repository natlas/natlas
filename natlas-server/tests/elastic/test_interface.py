from time import sleep

from config import Config
from app.elastic import ElasticInterface


def test_delete_by_query():
    client = ElasticInterface(Config().ELASTICSEARCH_URL)
    client.new_result({
        "ip": "127.0.0.1"
    })
    sleep(2)
    assert client.delete_host("127.0.0.1") == 2
