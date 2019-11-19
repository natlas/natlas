from netaddr import IPSet, IPNetwork
from app.scope.cyclicprng import CyclicPRNG


class IPScanManager:
	networks = []
	total = 0
	rng = None

	def __init__(self):
		self.networks = []
		self.total = 0
		self.rng = None

	def __init__(self, whitelist, blacklist):
		self.networks = []
		self.total = 0
		self.rng = None

		self.setWhitelist(whitelist)
		self.setBlacklist(blacklist)
		self.initializeManager()

	def setWhitelist(self, whitelist):
		self.white = IPSet([])
		for block in whitelist:
			self.white.add(IPNetwork(block))
			# Remove invalid broadcast and network addresses
			if block.broadcast is not None:
				self.white.remove(IPNetwork(block.broadcast))
			if block.size > 2:
				self.white.remove(IPNetwork(block.network))

	def setBlacklist(self, blacklist):
		self.black = IPSet([])
		for block in blacklist:
			self.black.add(IPNetwork(block))

	def initializeManager(self):
		self.networks = []
		self.ipset = self.white - self.black

		for block in self.ipset.iter_cidrs():
			self.total += block.size
			self.networks.append({"network": block, "size": block.size, "start": block[0], "index": 0})

		if self.total < 1:
			raise Exception("IPScanManager can not be started with an empty target scope")

		self.rng = CyclicPRNG(self.total)

		def blockcomp(b):
			return b["start"]

		self.networks.sort(key=blockcomp)

		start = 1
		for i in range(0, len(self.networks)):
			self.networks[i]["index"] = start
			start += self.networks[i]["size"]

		self.initialized = True

	def inWhitelist(self, ip):
		return ip in self.white

	def inBlacklist(self, ip):
		return ip in self.black

	def getTotal(self):
		return self.total

	def getReady(self):
		return self.rng and self.total > 0 and self.initialized

	def getNextIP(self):
		if self.rng:
			index = self.rng.getRandom()
			return self.getIP(index)
		else:
			return None

	def getIP(self, index):
		def binarysearch(networks, i):
			middle = int(len(networks) / 2)
			network = networks[middle]
			if i < network["index"]:
				return binarysearch(networks[:middle], i)
			elif i >= (network["index"] + network["size"]):
				return binarysearch(networks[middle + 1:], i)
			else:
				return network["network"][i - network["index"]]
		return binarysearch(self.networks, index)
