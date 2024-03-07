from datetime import datetime
from app.elastic.client import ElasticClient
from app.elastic.indices import ElasticIndices
import random
import sys


class ElasticInterface:
    client = None
    indices = None

    def __init__(
        self,
        elasticUrl: str,
        authEnabled: bool,
        elasticUser: str,
        elasticPassword: str,
        basename: str = "nmap",
    ):
        self.client = ElasticClient(
            elasticUrl,
            authEnabled=authEnabled,
            elasticUser=elasticUser,
            elasticPassword=elasticPassword,
        )
        self.indices = ElasticIndices(self.client, basename)

    def search(
        self, limit: int, offset: int, query: str = "nmap", searchIndex: str = "latest"
    ):
        """
        Execute a user supplied search and return the results
        """
        query = {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": query,
                            "fields": ["nmap_data"],
                            "default_operator": "AND",
                        }
                    },
                    {"term": {"is_up": True}},
                    {"range": {"port_count": {"gt": 0}}},
                ]
            }
        }
        sort = {"ctime": {"order": "desc"}}

        return self.client.get_collection(
            index=self.indices.name(searchIndex),
            query=query,
            sort=sort,
            from_=offset,
        )

    def total_hosts(self):
        """
        Count the number of documents in nmap and return the count
        """
        result = self.client.execute_count(index=self.indices.name("latest"))
        return result["count"]

    def new_result(self, host: dict):
        """
        Create new elastic documents in both indices for a new scan result
        """
        ip = str(host["ip"])

        self.client.execute_index(index=self.indices.name("history"), document=host)
        self.client.execute_index(
            index=self.indices.name("latest"), id=ip, document=host
        )
        return True

    def get_host(self, ip: str):
        """
        Gets the most recent result for a host, but by querying the nmap_history it also gives us the total number of historical results
        """

        size = 1
        query = {"term": {"ip": ip}}
        sort = {"ctime": {"order": "desc"}}

        return self.client.get_single_host(
            index=self.indices.name("history"), size=size, query=query, sort=sort
        )

    def get_host_history(self, ip: str, limit: int, offset: int):
        """
        Gets a collection of historical results for a specific ip address
        """
        query = {"term": {"ip": ip}}
        sort = {"ctime": {"order": "desc"}}

        return self.client.get_collection(
            index=self.indices.name("history"),
            size=limit,
            from_=offset,
            query=query,
            sort=sort,
        )

    def count_host_screenshots(self, ip: str):
        """
        Search history for an ip address and returns the number of historical screenshots
        """
        query = {"term": {"ip": ip}}
        aggs = {"screenshot_count": {"sum": {"field": "num_screenshots"}}}

        # By setting size to 0, _source to False, and track_scores to False, we're able to optimize this query to give us only what we care about
        result = self.count_scans_matching(query=query, aggs=aggs)
        return int(result["aggregations"]["screenshot_count"]["value"])

    def get_host_screenshots(self, ip: str, limit: int, offset: int):
        """
        Gets screenshots and minimal context for a given host
        """
        query = {
            "bool": {
                "must": [
                    {"term": {"ip": ip}},
                    {"range": {"num_screenshots": {"gt": 0}}},
                ]
            }
        }
        sort = {"ctime": {"order": "desc"}}
        source_fields = ["screenshots", "ctime", "scan_id"]
        return self.client.get_collection(
            index=self.indices.name("history"),
            query=query,
            size=limit,
            from_=offset,
            sort=sort,
            _source=source_fields,
            track_scores=False,
        )

    def get_host_by_scan_id(self, scan_id: str):
        """
        Get a specific historical result based on scan_id, which should be unique
        """

        size = 1
        query = {
            "query_string": {
                "query": scan_id,
                "fields": ["scan_id"],
                "default_operator": "AND",
            }
        }
        sort = {"ctime": {"order": "desc"}}

        return self.client.get_single_host(
            index=self.indices.name("history"), size=size, query=query, sort=sort
        )

    def delete_scan(self, scan_id: str):
        """
        Delete a specific scan, if it's the most recent then try to migrate the next oldest back into the latest index
        """
        migrate = False
        size = 1
        query = {"query_string": {"query": scan_id, "fields": ["scan_id"]}}
        sort = {"ctime": {"order": "desc"}}
        count, host = self.client.get_single_host(
            index=self.indices.name("latest"), size=size, query=query, sort=sort
        )
        if count != 0:
            # we're deleting the most recent scan result and need to pull the next most recent into the nmap index
            # otherwise you won't find the host when doing searches or browsing
            ipaddr = host["ip"]
            size = 2
            query = {"query_string": {"query": ipaddr, "fields": ["ip"]}}
            sort = {"ctime": {"order": "desc"}}

            count, twoscans = self.client.get_collection(
                index=self.indices.name("history"), size=size, query=query, sort=sort
            )
            # If count is one then there's only one result in history so we can just delete it.
            # If count is > 1 then we need to migrate the next oldest scan data
            if count > 1:
                migrate = True
        deleteBody = {
            "query": {
                "query_string": {
                    "query": scan_id,
                    "fields": ["scan_id"],
                    "default_operator": "AND",
                }
            }
        }
        result = self.client.execute_delete_by_query(
            index=self.indices.str_indices(), body=deleteBody
        )
        if migrate:
            self.client.execute_index(
                index=self.indices.name("latest"), id=ipaddr, document=twoscans[1]
            )
        return result["deleted"]

    def delete_host(self, ip: str):
        """
        Delete all occurrences of a given ip address
        """
        deleteBody = {
            "query": {
                "query_string": {
                    "query": ip,
                    "fields": ["ip", "id"],
                    "default_operator": "AND",
                }
            }
        }

        deleted = self.client.execute_delete_by_query(
            index=self.indices.str_indices(), body=deleteBody
        )
        return deleted["deleted"]

    def random_host(self):
        """
        Get a random single host and return it
        """
        seed = random.randrange(sys.maxsize)
        offset = 0
        size = 1
        query = {
            "function_score": {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"is_up": True}},
                            {"range": {"port_count": {"gt": 0}}},
                        ]
                    }
                },
                "random_score": {"seed": seed, "field": "_seq_no"},
            }
        }

        count, host = self.client.get_single_host(
            index=self.indices.name("latest"), size=size, from_=offset, query=query
        )
        return host

    def get_current_screenshots(self, limit: int, offset: int):
        """
        Get all current screenshots
        """
        query = {"range": {"num_screenshots": {"gt": 0}}}
        aggs = {"screenshot_count": {"sum": {"field": "num_screenshots"}}}
        sort = {"ctime": {"order": "desc"}}
        source_fields = ["screenshots", "ctime", "scan_id", "ip"]
        # We need to execute_search instead of get_collection here because we also need the aggregation information
        result = self.client.execute_search(
            index=self.indices.name("latest"),
            query=query,
            size=limit,
            from_=offset,
            aggs=aggs,
            sort=sort,
            _source=source_fields,
            track_scores=False,
        )
        num_screenshots = int(result["aggregations"]["screenshot_count"]["value"])
        results = self.client.collate_source(result["hits"]["hits"])

        return result["hits"]["total"], num_screenshots, results

    def count_scans_since(self, timestamp: datetime):
        """
        Count the number of scans that started after a given timestamp
        """
        query = {"range": {"scan_start": {"gte": timestamp}}}
        return self.count_scans_matching(query=query)["hits"]["total"]

    def count_scans_matching(self, index: str = "history", **kwargs):
        """
        Count the number of scans that match an arbitrary search body
        """
        return self.client.execute_search(
            index=self.indices.name(index), size=0, track_scores=False, **kwargs
        )
