from collections import Counter
from itertools import combinations


def detect_change_types(initial: list[float], final: list[float]) -> list[str]:
    initial_sorted = sorted(initial, reverse=True)
    final_sorted = sorted(final, reverse=True)

    if initial_sorted == final_sorted:
        return ["ACCEPTED"]

    initial_counts = Counter(initial_sorted)
    final_counts = Counter(final_sorted)

    is_superset = _is_multiset_superset(final_counts, initial_counts)
    is_subset = _is_multiset_superset(initial_counts, final_counts)

    types = []
    if is_superset and not is_subset:
        types.append("ADD")
    elif is_subset and not is_superset:
        types.append("REMOVE")

    if len(initial_sorted) == len(final_sorted) and initial_counts != final_counts:
        types.append("RESIZE")
        if not (initial_counts & final_counts):
            # No batch value survived unchanged -- this reads as a full
            # replacement, not just a resize. Matches the assignment's own
            # example: [1000,1000,400] -> [800,800,800] is ["RESIZE","REPLACED"].
            types.append("REPLACED")

    if len(final_sorted) > len(initial_sorted) and _some_batch_was_split(initial_sorted, final_sorted):
        types.append("SPLIT")

    if len(final_sorted) < len(initial_sorted) and _some_batch_was_split(final_sorted, initial_sorted):
        types.append("MERGE")

    if not types:
        types.append("REPLACED")

    return types


def count_changed_batches(initial: list[float], final: list[float]) -> int:
    # Pairwise diff over sorted, zero-padded plans: how many batch "slots"
    # ended up a different size. E.g. [1000,1000,400] -> [800,800,800] is 3,
    # even though only two change *types* (RESIZE, REPLACED) apply overall.
    initial_sorted = sorted(initial, reverse=True)
    final_sorted = sorted(final, reverse=True)

    length = max(len(initial_sorted), len(final_sorted))
    initial_padded = initial_sorted + [0.0] * (length - len(initial_sorted))
    final_padded = final_sorted + [0.0] * (length - len(final_sorted))

    return sum(1 for a, b in zip(initial_padded, final_padded) if a != b)


def _is_multiset_superset(a: Counter, b: Counter) -> bool:
    return all(a[value] >= count for value, count in b.items())


def _some_batch_was_split(smaller: list[float], larger: list[float]) -> bool:
    # True if some subset (size >= 2) of `larger` sums to a value present in
    # `smaller`, and the remaining elements on both sides match exactly.
    smaller_counts = Counter(smaller)
    indices = range(len(larger))

    for size in range(2, len(larger) + 1):
        for combo in combinations(indices, size):
            combo_sum = sum(larger[i] for i in combo)
            if smaller_counts[combo_sum] <= 0:
                continue
            remaining_smaller = smaller_counts.copy()
            remaining_smaller[combo_sum] -= 1
            remaining_larger = Counter(larger[i] for i in indices if i not in combo)
            if remaining_smaller == remaining_larger:
                return True
    return False
