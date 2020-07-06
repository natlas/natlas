import timeit

from app.scope.cyclicprng import CyclicPRNG


def test_random_cycle(app):
    cycle_size = 10
    c = CyclicPRNG(cycle_size)
    first_cycle = [c.get_random() for _ in range(cycle_size)]
    second_cycle = [c.get_random() for _ in range(cycle_size)]
    assert first_cycle != second_cycle


def test_consistent_cycle(app):
    cycle_size = 10
    c = CyclicPRNG(cycle_size, True)
    first_cycle = [c.get_random() for _ in range(cycle_size)]
    second_cycle = [c.get_random() for _ in range(cycle_size)]
    assert first_cycle == second_cycle


def test_cycle_init_time(app):
    """
        Sanity checking that the prng can be initialized in a reasonable time.
        ip4_addr_space = 4294967296
        ip6_addr_space = 340282366920938463463374607431768211456
    """
    ip4_timer = timeit.Timer(
        "CyclicPRNG(4294967296)", setup="from app.scope.cyclicprng import CyclicPRNG"
    )
    ip6_timer = timeit.Timer(
        "CyclicPRNG(340282366920938463463374607431768211456)",
        setup="from app.scope.cyclicprng import CyclicPRNG",
    )
    assert all(i < 0.5 for i in ip4_timer.repeat(10, 1))
    assert all(i < 0.5 for i in ip6_timer.repeat(10, 1))


def test_size_one_cycle(app):
    """
        Edge case: In cycles of size one, [1] is the only valid cycle
    """
    cycle_size = 1
    c = CyclicPRNG(cycle_size)
    first_cycle = [c.get_random() for _ in range(cycle_size)]
    second_cycle = [c.get_random() for _ in range(cycle_size)]
    assert len(first_cycle) == len(second_cycle) == 1
    assert first_cycle == second_cycle == [1]


def test_size_two_cycle(app):
    """
        Edge case: In cycles of size 2, we expect results to always alternate
        i.e. [1,2,1,2] or [2,1,2,1] instead of [1,2,2,1] or [2,1,1,2]
    """
    cycle_size = 2
    c = CyclicPRNG(cycle_size)
    first_cycle = [c.get_random() for _ in range(cycle_size)]
    second_cycle = [c.get_random() for _ in range(cycle_size)]
    assert len(first_cycle) == len(second_cycle) == 2
    assert first_cycle == second_cycle
