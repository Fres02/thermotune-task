from app.services.generate import generate_plans


def test_generates_at_least_one_plan_for_2400kg():
    plans = generate_plans(2400, [500, 800, 1000], 400, 1000)
    assert len(plans) > 0


def test_known_valid_plans_are_present():
    plans = {tuple(p) for p in generate_plans(2400, [500, 800, 1000], 400, 1000)}
    assert (800, 800, 800) in plans
    assert (1000, 1000, 400) in plans


def test_known_invalid_combinations_never_appear():
    plans = {tuple(p) for p in generate_plans(2400, [500, 800, 1000], 400, 1000)}
    assert (1200, 1200) not in plans
    assert tuple(sorted([1000, 1000, 300, 100], reverse=True)) not in plans


def test_every_plan_sums_to_the_order_quantity():
    plans = generate_plans(2400, [500, 800, 1000], 400, 1000)
    for plan in plans:
        assert abs(sum(plan) - 2400) < 1e-6


def test_no_batch_violates_bounds():
    plans = generate_plans(2400, [500, 800, 1000], 400, 1000)
    for plan in plans:
        assert all(400 - 1e-9 <= batch <= 1000 + 1e-9 for batch in plan)


def test_no_duplicate_plans_regardless_of_batch_order():
    plans = generate_plans(2400, [500, 800, 1000], 400, 1000)
    canonical = [tuple(sorted(plan, reverse=True)) for plan in plans]
    assert len(canonical) == len(set(canonical))


def test_impossible_order_returns_no_plans():
    # 500kg order, minimum batch 600kg: no combination can ever reach 500kg.
    plans = generate_plans(500, [], 600, 1000)
    assert plans == []


def test_node_limit_terminates_without_crashing():
    plans = generate_plans(100_000, [], 1, 100_000, step=1, node_limit=200)
    assert isinstance(plans, list)
