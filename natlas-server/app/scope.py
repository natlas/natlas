import ipaddress

class ScopeManager():
  
  scope = []
  blacklist = []
  scopeSize = 0
  blacklistSize = 0

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
      newItem = ipaddress.ip_network(item.target)
      self.scope.append(newItem)
      newScopeSize += newItem.num_addresses
    self.scopeSize = newScopeSize
    print("Scope Size: %s" % self.scopeSize)

  def updateBlacklist(self):
    from app.models import ScopeItem
    newBlacklistSize = 0
    for item in ScopeItem.getBlacklist():
      newItem = ipaddress.ip_network(item.target)
      self.blacklist.append(newItem)
      newBlacklistSize += newItem.num_addresses
    self.blacklistSize = newBlacklistSize
    print("Blacklist Size: %s" % self.blacklistSize)

  def update(self):
    from app.models import ScopeItem
    self.updateScope()

    self.updateBlacklist()