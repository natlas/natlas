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
