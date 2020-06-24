# importing these here allows for "from app.elastic import ElasticInterface" instead of "from app.elastic.interface import ElasticInterface"
from app.elastic.client import ElasticClient  # noqa: F401
from app.elastic.interface import ElasticInterface  # noqa: F401
