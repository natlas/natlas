import json
import logging

from config import Config

from app.elastic.client import ElasticClient


class ElasticIndices:
    basename = None  # type: ignore[var-annotated]
    indices = None  # type: ignore[var-annotated]
    logger = logging.getLogger("elasticsearch")
    logger.setLevel("ERROR")

    def __init__(self, client: ElasticClient, basename: str):
        self.basename = basename
        self.client = client
        self.indices = {"latest": basename, "history": f"{basename}_history"}
        self._initialize_indices()

    def _initialize_indices(self):  # type: ignore[no-untyped-def]
        """
        Ensure each index in this context is initalized
        """
        with open(Config().BASEDIR + "/defaults/elastic/mapping.json") as mapfile:
            mapping = json.loads(mapfile.read())
        for index in self.all_indices():
            self.client.initialize_index(index, mapping)
        self.logger.info(f"Initialized Elasticsearch {self.basename} indices")

    def _delete_indices(self):  # type: ignore[no-untyped-def]
        """
        Delete all indices in this context
        """
        for index in self.all_indices():
            self.client.delete_index(index=index)
        self.logger.info(f"Deleted Elasticsearch {self.basename} indices")

    def name(self, alias: str):  # type: ignore[no-untyped-def]
        """
        Get the name of an index based on the current context
        """
        return self.indices[alias]  # type: ignore[index]

    def all_indices(self):  # type: ignore[no-untyped-def]
        """
        Return a list of indices in the current context
        """
        return [v for _, v in self.indices.items()]  # type: ignore[union-attr]

    def str_indices(self):  # type: ignore[no-untyped-def]
        """
        Return a comma-separated string of indices in the current context
        """
        return ",".join(self.all_indices())
