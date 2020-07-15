from netaddr import IPSet, IPNetwork
from cyclicprng import CyclicPRNG
from app import db
from app.models import ScopeLog


class IPScanManager:
    networks = []
    total = 0
    rng = None
    consistent = None

    def __init__(self, whitelist, blacklist, consistent: bool):
        self.networks = []
        self.total = 0
        self.rng = None
        self.consistent = consistent
        self.set_whitelist(whitelist)
        self.set_blacklist(blacklist)
        self.initialize_manager()

    def log_to_db(self, message):
        log_messages = {
            "init": "PRNG Starting Up",
            "restart": "PRNG Cycle Restarted",
            "default": "Unknown PRNG Event",
        }
        db_log = ScopeLog(log_messages.get(message, "default"))
        db.session.add(db_log)
        db.session.commit()

    def set_whitelist(self, whitelist):
        self.whitelist = IPSet([])
        for block in whitelist:
            self.whitelist.add(IPNetwork(block))
            # Remove invalid broadcast and network addresses
            if block.broadcast is not None:
                self.whitelist.remove(IPNetwork(block.broadcast))
            if block.size > 2:
                self.whitelist.remove(IPNetwork(block.network))

    def set_blacklist(self, blacklist):
        self.blacklist = IPSet([])
        for block in blacklist:
            self.blacklist.add(IPNetwork(block))

    def initialize_manager(self):
        self.networks = []
        self.ipset = self.whitelist - self.blacklist

        for block in self.ipset.iter_cidrs():
            self.total += block.size
            self.networks.append(
                {"network": block, "size": block.size, "start": block[0], "index": 0}
            )

        if self.total < 1:
            raise Exception(
                "IPScanManager can not be started with an empty target scope"
            )

        self.rng = CyclicPRNG(
            self.total, consistent=self.consistent, event_handler=self.log_to_db
        )

        def blockcomp(b):
            return b["start"]

        self.networks.sort(key=blockcomp)

        start = 1
        for i in range(0, len(self.networks)):
            self.networks[i]["index"] = start
            start += self.networks[i]["size"]

        self.initialized = True

    def in_whitelist(self, ip):
        return ip in self.whitelist

    def in_blacklist(self, ip):
        return ip in self.blacklist

    def get_total(self):
        return self.total

    def get_ready(self):
        return self.rng and self.total > 0 and self.initialized

    def get_next_ip(self):
        if self.rng:
            index = self.rng.get_random()
            return self.get_ip(index)
        else:
            return None

    def get_ip(self, index):
        def binarysearch(networks, i):
            middle = int(len(networks) / 2)
            network = networks[middle]
            if i < network["index"]:
                return binarysearch(networks[:middle], i)
            elif i >= (network["index"] + network["size"]):
                return binarysearch(networks[middle + 1 :], i)
            else:
                return network["network"][i - network["index"]]

        return binarysearch(self.networks, index)
