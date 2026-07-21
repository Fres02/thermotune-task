EPSILON = 1e-9


def _build_candidates(
    minimum_batch_size_kg: float,
    maximum_batch_size_kg: float,
    available_batch_sizes_kg: list[float],
    step: float,
) -> list[float]:
    candidates = set(available_batch_sizes_kg)
    candidates.add(minimum_batch_size_kg)
    candidates.add(maximum_batch_size_kg)

    size = minimum_batch_size_kg
    while size <= maximum_batch_size_kg + EPSILON:
        candidates.add(round(size, 6))
        size += step

    in_range = [c for c in candidates if minimum_batch_size_kg - EPSILON <= c <= maximum_batch_size_kg + EPSILON]
    return sorted(in_range, reverse=True)


def generate_plans(
    order_quantity_kg: float,
    available_batch_sizes_kg: list[float],
    minimum_batch_size_kg: float,
    maximum_batch_size_kg: float,
    step: float = 50.0,
    node_limit: int = 5000,
) -> list[list[float]]:
    candidates = _build_candidates(
        minimum_batch_size_kg, maximum_batch_size_kg, available_batch_sizes_kg, step
    )
    if not candidates:
        return []

    seen: set[tuple[float, ...]] = set()
    plans: list[list[float]] = []
    nodes_explored = 0

    def search(remaining: float, plan: list[float]) -> None:
        nonlocal nodes_explored
        if nodes_explored >= node_limit:
            return
        nodes_explored += 1

        if remaining < EPSILON:
            key = tuple(sorted(plan, reverse=True))
            if key not in seen:
                seen.add(key)
                plans.append(list(key))
            return

        if remaining < minimum_batch_size_kg - EPSILON:
            return  # dead end: no legal batch can close this out

        for candidate in candidates:
            if candidate <= remaining + EPSILON:
                search(remaining - candidate, plan + [candidate])

    search(order_quantity_kg, [])
    return plans
