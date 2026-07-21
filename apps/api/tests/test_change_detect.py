from app.services.change_detect import count_changed_batches, detect_change_types


def test_accepted_when_plans_are_identical_regardless_of_order():
    assert detect_change_types([800, 800, 800], [800, 800, 800]) == ["ACCEPTED"]
    assert detect_change_types([1000, 500, 900], [900, 1000, 500]) == ["ACCEPTED"]


def test_resize_and_replaced_matches_the_assignment_worked_example():
    # §6.4: initial [1000,1000,400] -> final [800,800,800] is ["RESIZE", "REPLACED"],
    # since every batch value changed and nothing carried over unchanged.
    types = detect_change_types([1000, 1000, 400], [800, 800, 800])
    assert types == ["RESIZE", "REPLACED"]


def test_resize_without_replaced_when_one_batch_is_kept():
    # Same batch count, different values, but the 800 batch survives untouched.
    types = detect_change_types([800, 1000, 600], [800, 900, 700])
    assert types == ["RESIZE"]


def test_split_when_one_batch_becomes_two():
    types = detect_change_types([800, 800, 800], [800, 800, 400, 400])
    assert "SPLIT" in types


def test_merge_when_two_batches_become_one():
    types = detect_change_types([800, 800, 400, 400], [800, 800, 800])
    assert "MERGE" in types


def test_add_when_final_is_a_strict_superset():
    assert detect_change_types([800, 800], [800, 800, 400]) == ["ADD"]


def test_remove_when_final_is_a_strict_subset():
    assert detect_change_types([800, 800, 400], [800, 800]) == ["REMOVE"]


def test_replaced_when_no_other_relationship_applies():
    # Different batch counts, no subset/superset relationship, no split/merge.
    types = detect_change_types([1000, 500, 500], [700, 700, 600, 400])
    assert types == ["REPLACED"]


def test_count_changed_batches_matches_the_assignment_example():
    assert count_changed_batches([1000, 1000, 400], [800, 800, 800]) == 3


def test_count_changed_batches_is_zero_when_accepted():
    assert count_changed_batches([800, 800, 800], [800, 800, 800]) == 0
