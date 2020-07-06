from threading import Lock
import random
import sympy
from datetime import datetime

from app import db
from app.models import ScopeLog

mutex = Lock()


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
    db_log = ScopeLog(message)
    db.session.add(db_log)
    db.session.commit()


class CyclicPRNG:
    """
        For more information about the existence of this class and why it does what it does,
        see https://github.com/natlas/natlas/wiki/Host-Coverage-Scanning-Strategy
        Edge case behavior:
            size = 1 -> Always return 1
            size = 2 -> The generator is always 2
    """

    size = 0
    Modulus = 0
    ModulusFactors = {}
    generator = 0
    start = 0
    end = 0
    current = 0
    cycle_start_time = None
    completed_cycle_count = 0
    consistent = False

    def __init__(self, cycle_size: int, consistent: bool = False):
        """
            Initialize PRNG that restarts after cycle_size calls
        """
        self.size = cycle_size
        if self.size > 1:
            self.init_cyclic_group()
            self.init_generator()
            self.init_permutation()
            self.cycle_start_time = datetime.utcnow()
            self.consistent = consistent
        if self.size < 1:
            raise Exception(
                "Random Number Generator must be given a positive non-zero integer"
            )

        log("PRNG Starting Up")

    def init_cyclic_group(self):
        def next_prime(num):
            num = num + 1 if (num % 2) == 0 else num + 2
            while not sympy.isprime(num):
                num = num + 2
            return num

        self.Modulus = next_prime(self.size)
        self.ModulusFactors = sympy.factorint(self.Modulus - 1)

    def init_generator(self):
        """
            Find a generator for the whole cyclic group.
        """
        found = False
        base = 0
        """
            If Modulus is 3 then the only generator we can use is 2.
            Otherwise we infinite loop because always self.generator == base
        """
        if self.Modulus == 3:
            self.generator = 2
            return
        while not found:
            base = random.randint(2, self.Modulus - 1)
            found = self.generator != base and all(
                modexp(base, int((self.Modulus - 1) / factor), self.Modulus) != 1
                for factor in self.ModulusFactors
            )
        self.generator = base

    def _cycle_until_in_range(self, element):
        """
            Cycle the element until it is self.size or less
        """
        while element > self.size:
            element = (element * self.generator) % self.Modulus
        return element

    def init_permutation(self):  # sourcery skip: use-assigned-variable
        """
            Create a new permutation of the scope
        """
        exp = random.randint(2, self.Modulus - 1)
        self.end = self._cycle_until_in_range(modexp(self.generator, exp, self.Modulus))
        self.start = self._cycle_until_in_range(
            (self.end * self.generator) % self.Modulus
        )
        self.current = self.start

    def restart_cycle(self):
        """
            Restart PRNG Cycle
        """
        if self.consistent:
            self.current = self.start
        else:
            self.init_generator()
            self.init_permutation()
        self.cycle_start_time = datetime.utcnow()
        self.completed_cycle_count += 1
        log("PRNG Cycle Restarted")

    def get_random(self):
        """
            Gets the next random number from the permutation
        """
        if self.size <= 1:
            return 1
        mutex.acquire()
        value = self.current
        self.current = self._cycle_until_in_range(
            (self.current * self.generator) % self.Modulus
        )
        if value == self.end:
            self.restart_cycle()
        mutex.release()
        return value
