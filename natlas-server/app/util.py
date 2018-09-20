import ipaddress
from app.models import ScopeItem
from app import elastic, ScopeManager


def hostinfo(ip):
    hostinfo = {}
    count, context = elastic.gethost(ip)
    if count == 0:
        return abort(404)
    hostinfo['history'] = count
    headshots = 0
    headshotTypes = ['headshot', 'vncheadshot',
                     'httpheadshot', 'httpsheadshot']
    for hs in headshotTypes:
        if context.get(hs):
            headshots += 1
    hostinfo['headshots'] = headshots
    if context.get('hostname'):
        hostinfo['hostname'] = context.get('hostname')
    return hostinfo, context


def isAcceptableTarget(target):
    targetAddr = ipaddress.IPv4Address(target)
    inScope = False

    for network in ScopeManager.getScope():
        if str(network).endswith('/32'):
            if targetAddr == ipaddress.IPv4Address(str(network).split('/32')[0]):
                inScope = True
        if targetAddr in list(network.hosts()):
            inScope = True

    if not inScope:
        return False

    for network in ScopeManager.getBlacklist():
        if str(network).endswith('/32'):
            if targetAddr == ipaddress.IPv4Address(str(network).split('/32')[0]):
                return False
        if targetAddr in list(network.hosts()):
            return False

    return True
