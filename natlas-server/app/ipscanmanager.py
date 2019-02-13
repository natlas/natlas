from netaddr import *
from app.cyclicprng import *

class IPScanManager:
	networks = []
	total = 0
	rng = None

	def __init__(self, whitelist, blacklist):
		set = IPSet([])
		for block in whitelist:
			set.add(IPNetwork(block))
		for block in blacklist:
			set.remove(IPNetwork(block))
		for block in set.iter_cidrs():
			self.total += block.size
			self.networks.append( { "network": block, "size": block.size, "start": block[0], "index": 0 } )

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

	def getTotal(self):
		return self.total

	def getNextIP(self):
		def binarysearch(networks, i):
			middle = int(len(networks)/2)
			network = networks[middle]
			if i < network["index"]:
				return binarysearch(networks[:middle], i)
			elif i >= (network["index"] + network["size"]):
				return binarysearch(networks[middle+1:], i)
			else:
				return network["network"][i - network["index"]]
		index = self.rng.getRandom()
		return binarysearch(self.networks, index)

	def getIP(self, index):
		def binarysearch(networks, i):
			middle = int(len(networks)/2)
			network = networks[middle]
			if i < network["index"]:
				return binarysearch(networks[:middle], i)
			elif i >= (network["index"] + network["size"]):
				return binarysearch(networks[middle+1:], i)
			else:
				return network["network"][i - network["index"]]
		return binarysearch(self.networks, index)
