import ipaddress
from datetime import datetime, timezone

def hostinfo(ip):
    from flask import current_app, abort
    hostinfo = {}
    count, context = current_app.elastic.gethost(ip)
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
    from flask import current_app, abort
    targetAddr = ipaddress.IPv4Address(target)
    inScope = False
    # if zero, update to make sure that the scopemanager has been populated
    if current_app.ScopeManager.getScopeSize() == 0: 
        current_app.ScopeManager.update()
        scopeSize = current_app.ScopeManager.getScopeSize()
        blacklistSize = current_app.ScopeManager.getBlacklistSize()
    for network in current_app.ScopeManager.getScope():
        if str(network).endswith('/32'):
            if targetAddr == ipaddress.IPv4Address(str(network).split('/32')[0]):
                inScope = True
        if targetAddr in network:
            inScope = True

    if not inScope:
        return False

    for network in current_app.ScopeManager.getBlacklist():
        if str(network).endswith('/32'):
            if targetAddr == ipaddress.IPv4Address(str(network).split('/32')[0]):
                return False
        if targetAddr in network:
            return False

    return True

def utcnow_tz():
    return datetime.now(timezone.utc)
