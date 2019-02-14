import ipaddress
from netaddr import IPNetwork
from app.ipscanmanager import IPScanManager

class ScopeManager():

    scope = []
    blacklist = []
    scopeSize = 0
    blacklistSize = 0
    scanmanager = None

    def __init__(self):
        self.scope = []
        self.blacklist = []

    def getScopeSize(self):
        return self.scopeSize

    def getBlacklistSize(self):
        return self.blacklistSize

    def getScope(self):
        return self.scope

    def getBlacklist(self):
        return self.blacklist

    def updateScope(self):
        from app.models import ScopeItem
        newScopeSize = 0
        for item in ScopeItem.getScope():
            newItem = ipaddress.ip_network(item.target, False)
            self.scope.append(newItem)
            newScopeSize += newItem.num_addresses
        self.scopeSize = newScopeSize
        #print("Scope Size: %s" % self.scopeSize)

    def updateBlacklist(self):
        from app.models import ScopeItem
        newBlacklistSize = 0
        for item in ScopeItem.getBlacklist():
            newItem = ipaddress.ip_network(item.target, False)
            self.blacklist.append(newItem)
            newBlacklistSize += newItem.num_addresses
        self.blacklistSize = newBlacklistSize
        #print("Blacklist Size: %s" % self.blacklistSize)

    def updateScanManager(self):
        from app.models import ScopeItem
        self.scanmanager = None
        self.scanmanager = IPScanManager([IPNetwork(n.target) for n in ScopeItem.getScope()], [IPNetwork(n.target) for n in ScopeItem.getBlacklist()])

    def getScanManager(self):
        return self.scanmanager

    def update(self):
        self.updateScope()
        self.updateBlacklist()
        self.updateScanManager()
        print("ScopeManager Updated")
