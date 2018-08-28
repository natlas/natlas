import ipaddress

class ScopeManager():
  
  scope = []
  blacklist = []

  def __init__(self):
    self.scope = []
    self.blacklist = []

  def getScope(self):
    return self.scope

  def getBlacklist(self):
    return self.blacklist

  def updateScope(self):
    from app.models import ScopeItem
    for item in ScopeItem.getScope():
      self.scope.append(ipaddress.ip_network(item.target))

  def updateBlacklist(self):
    from app.models import ScopeItem
    for item in ScopeItem.getBlacklist():
      self.blacklist.append(ipaddress.ip_network(item.target))

  def update(self):
    from app.models import ScopeItem
    for item in ScopeItem.getScope():
      self.scope.append(ipaddress.ip_network(item.target))

    for item in ScopeItem.getBlacklist():
      self.blacklist.append(ipaddress.ip_network(item.target))