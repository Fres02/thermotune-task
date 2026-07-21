QUANTITY_WEIGHT = 0.8
STRUCTURE_WEIGHT = 0.2


def compute_similarity(initial: list[float], final: list[float], order_quantity_kg: float) -> float:
    initial_sorted = sorted(initial, reverse=True)
    final_sorted = sorted(final, reverse=True)

    length = max(len(initial_sorted), len(final_sorted))
    initial_padded = initial_sorted + [0.0] * (length - len(initial_sorted))
    final_padded = final_sorted + [0.0] * (length - len(final_sorted))

    quantity_difference = sum(abs(a - b) for a, b in zip(initial_padded, final_padded))
    quantity_similarity = (
        1 - quantity_difference / (2 * order_quantity_kg) if order_quantity_kg > 0 else 0.0
    )

    count_initial, count_final = len(initial), len(final)
    longest = max(count_initial, count_final)
    structure_similarity = 1 - abs(count_initial - count_final) / longest if longest > 0 else 1.0

    final_similarity = QUANTITY_WEIGHT * quantity_similarity + STRUCTURE_WEIGHT * structure_similarity
    return max(0.0, min(100.0, final_similarity * 100))
