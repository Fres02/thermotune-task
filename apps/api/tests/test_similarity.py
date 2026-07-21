from app.services.similarity import compute_similarity


def test_quantity_only_difference_matches_the_assignment_worked_example():
    # §7.3: initial [400,1000,1000] vs final [800,800,800] gives an 800kg total
    # difference and an 83.33% quantity-only similarity. compute_similarity blends
    # in a structure term (§7.4), so recompute the quantity-only figure directly
    # to check that part of the arithmetic in isolation.
    initial_sorted = sorted([400, 1000, 1000], reverse=True)
    final_sorted = sorted([800, 800, 800], reverse=True)
    order_qty = 2400

    difference = sum(abs(a - b) for a, b in zip(initial_sorted, final_sorted))
    quantity_similarity = 1 - difference / (2 * order_qty)

    assert difference == 800
    assert round(quantity_similarity * 100, 2) == 83.33


def test_combined_score_blends_quantity_and_structure():
    # Same example, but through the actual 0.8/0.2 blended formula (§7.4).
    result = compute_similarity([400, 1000, 1000], [800, 800, 800], 2400)
    assert round(result, 2) == 86.67


def test_identical_plans_are_100_percent_similar():
    assert compute_similarity([800, 800, 800], [800, 800, 800], 2400) == 100.0


def test_score_is_always_clamped_between_0_and_100():
    result = compute_similarity([2400], [1] * 50, 2400)
    assert 0.0 <= result <= 100.0


def test_padding_handles_different_batch_counts():
    result = compute_similarity([1200, 1200], [800, 800, 800], 2400)
    assert 0.0 <= result <= 100.0
