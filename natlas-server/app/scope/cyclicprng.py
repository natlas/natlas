from threading import Lock
import random
import sympy
from datetime import datetime
import os

from app import db
from app.models import ScopeLog

mutex = Lock()

LOGFILE = "logs/cyclicprng.log"


def modexp(b, e, m):
    bits = [(e >> bit) & 1 for bit in range(e.bit_length())]
    s = b
    v = 1
    for bit in bits:
        if bit == 1:
            v *= s
            v %= m
        s *= s
        s %= m
    return v


def log(message):
    if not os.path.isdir("logs"):
        os.makedirs("logs", exist_ok=True)
    with open(LOGFILE, "a") as f:
        f.write(f"{str(datetime.utcnow())} - {message}\n")
    db_log = ScopeLog(message)
    db.session.add(db_log)
    db.session.commit()


class CyclicPRNG:
    N = 0
    Modulus = 0
    ModulusFactors = {}
    G = 0
    start = 0
    end = 0
    current = 0
    cycle_start_time = None
    completed_cycle_count = 0

    def __init__(self, N):
        self.N = N
        if N > 1:
            self.init_cyclic_group()
            self.init_generator()
            self.init_permutation()
            self.cycle_start_time = datetime.utcnow()
        if N < 1:
            raise Exception(
                "Random Number Generator must be given a positive non-zero integer"
            )

        log("PRNG Starting Up")

    def get_n(self):
        return self.N

    def get_modulus(self):
        return self.Modulus

    def init_cyclic_group(self):
        def next_prime(num):
            num = num + 1 if (num % 2) == 0 else num + 2
            while not sympy.isprime(num):
                num = num + 2
            return num

        self.Modulus = next_prime(self.N)
        self.ModulusFactors = sympy.factorint(self.Modulus - 1)

    def init_generator(self):
        found = False
        while not found:
            base = random.randint(2, self.Modulus - 1)
            found = all(
                modexp(base, int((self.Modulus - 1) / factor), self.Modulus) != 1
                for factor in self.ModulusFactors
            )
        self.G = base

    def _cycle_until_in_range(self, element):
        """ Cycle the element until it is self.N or less """
        while element > self.N:
            element = (element * self.G) % self.Modulus
        return element

    def init_permutation(self):
        exp = random.randint(2, self.Modulus - 1)
        self.end = self._cycle_until_in_range(modexp(self.G, exp, self.Modulus))
        self.start = self._cycle_until_in_range((self.end * self.G) % self.Modulus)
        self.current = self.start

    def get_random(self):
        if self.N <= 1:
            return 1
        mutex.acquire()
        value = self.current
        self.current = self._cycle_until_in_range(
            (self.current * self.G) % self.Modulus
        )
        if value == self.end:
            log("PRNG Cycle Restarted")
            self.init_generator()
            self.init_permutation()
            self.cycle_start_time = datetime.utcnow()
            self.completed_cycle_count += 1
        mutex.release()
        return value
