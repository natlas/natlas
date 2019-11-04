import ipaddress
from netaddr import IPNetwork
from app.ipscanmanager import IPScanManager
from datetime import datetime
import os

LOGFILE = 'logs/scopemanager.log'


def log(message, printm=False):
	if not os.path.isdir('logs'):
		os.makedirs('logs', exist_ok=True)
	with open(LOGFILE, 'a') as f:
		f.write('%s - %s\n' % (str(datetime.now()), message))
	if printm:
		print('%s - %s\n' % (str(datetime.now()), message))


class ScopeManager():

	scope = []
	blacklist = []
	pendingRescans = []
	dispatchedRescans = []
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

	def getPendingRescans(self):
		return self.pendingRescans

	def getDispatchedRescans(self):
		return self.dispatchedRescans

	def getIncompleteScans(self):
		if self.pendingRescans == [] or self.dispatchedRescans == []:
			from app.models import RescanTask
			self.pendingRescans = RescanTask.getPendingTasks()
			self.dispatchedRescans = RescanTask.getDispatchedTasks()
		return self.pendingRescans + self.dispatchedRescans

	def updateDispatchedRescans(self):
		from app.models import RescanTask
		self.dispatchedRescans = RescanTask.getDispatchedTasks()

	def updatePendingRescans(self):
		from app.models import RescanTask
		self.pendingRescans = RescanTask.getPendingTasks()

	def updateScope(self):
		from app.models import ScopeItem
		newScopeSize = 0
		newScope = []
		for item in ScopeItem.getScope():
			newItem = ipaddress.ip_network(item.target, False)
			newScope.append(newItem)
			newScopeSize += newItem.num_addresses
		self.scope = newScope
		self.scopeSize = newScopeSize

	def updateBlacklist(self):
		from app.models import ScopeItem
		newBlacklistSize = 0
		newBlacklist = []
		for item in ScopeItem.getBlacklist():
			newItem = ipaddress.ip_network(item.target, False)
			newBlacklist.append(newItem)
			newBlacklistSize += newItem.num_addresses
		self.blacklist = newBlacklist
		self.blacklistSize = newBlacklistSize

	def updateScanManager(self):
		from app.models import ScopeItem
		self.scanmanager = None
		try:
			scanrange = [IPNetwork(n.target) for n in ScopeItem.getScope()]
			blacklistrange = [IPNetwork(n.target) for n in ScopeItem.getBlacklist()]
			self.scanmanager = IPScanManager(scanrange, blacklistrange)
		except Exception:
			log("Scan manager could not be instantiated because there was no scope configured.", printm=True)

	def getScanManager(self):
		return self.scanmanager

	def update(self):
		self.updateScope()
		self.updateBlacklist()
		self.updateScanManager()
		log("ScopeManager Updated")

	def address_in_collection(self, targetAddr, networkCollection):
		""" Take in a collection of networks, identify if the target address is in one of those networks """
		inCollection = False
		for network in networkCollection:
			# TODO this eventually needs to be upgraded to support IPv6
			if str(network).endswith('/32') and targetAddr == ipaddress.IPv4Address(str(network).split('/32')[0]):
				inCollection = True
			if targetAddr in network:
				inCollection = True
		return inCollection

	def isAcceptableTarget(self, target):
		# Ensure it's a valid IPv4Address
		try:
			# TODO this eventually needs to be upgraded to support IPv6
			targetAddr = ipaddress.IPv4Address(target)
		except ipaddress.AddressValueError:
			return False

		# if zero, update to make sure that the scopemanager has been populated
		if self.getScopeSize() == 0:
			self.update()

		inScope = self.address_in_collection(targetAddr, self.getScope())

		# Address doesn't fall in scope ranges
		if not inScope:
			return False

		inBlacklist = self.address_in_collection(targetAddr, self.getBlacklist())

		# Address falls in blacklist ranges
		if inBlacklist:
			return False

		# Address is in scope and not blacklisted
		return True
