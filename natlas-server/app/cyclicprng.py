from threading import Lock
import random
import sympy

mutex = Lock()

def modexp(b, e, m):
        bits = [(e >> bit) & 1 for bit in range(0, e.bit_length())]
        s = b
        v = 1
        for bit in bits:
                if bit == 1:
                        v *= s
                        v %= m
                s *= s
                s %= m
        return v

class CyclicPRNG:
	N = 0
	Modulus = 0
	ModulusFactors = {}
	G = 0
	start = 0
	end = 0
	current = 0

	def __init__(self, N):
		self.N = N
		if N > 2:
			self.initCyclicGroup()
			self.initGenerator()
			self.initPermutation()
		if N < 1:
			raise Exception("Random Number Generator must be given a positive non-zero integer")

	def getN(self):
		return self.N

	def getModulus(self):
		return self.Modulus

	def initCyclicGroup(self):
		def next_prime(num):
			if (num % 2) == 0:
				num = num + 1
			else:
				num = num + 2
			while sympy.isprime(num) == False:
				num = num + 2
			return num
		self.Modulus = next_prime(self.N)
		self.ModulusFactors = sympy.factorint(self.Modulus-1)

	def initGenerator(self):
		found = False
		while found == False:
			base = random.randint(2, self.Modulus-2)
			found = True
			for factor in self.ModulusFactors:
				if modexp(base, int((self.Modulus-1)/factor), self.Modulus) == 1:
					found = False
					break
		self.G = base

	def initPermutation(self):
		exp = random.randint(2, self.Modulus-1)
		self.end = modexp(self.G, exp, self.Modulus)
		while self.end > self.N:
			self.end = (self.end * self.G) % self.Modulus

		self.start = (self.end * self.G) % self.Modulus
		while self.start > self.N:
			self.start = (self.start * self.G) % self.Modulus
		self.current = self.start

	def getRandom(self):
		if self.N <= 2:
			return random.randint(1,self.N)
		mutex.acquire()
		value = self.current
		self.current = (self.current * self.G) % self.Modulus
		while self.current > self.N:
			self.current = (self.current * self.G) % self.Modulus
		if value == self.end:
			self.initGenerator()
			self.initPermutation()
		mutex.release()
		return value
