from app.services.types import OrderSpec

EPSILON = 1e-9


def validate_order_input(order: OrderSpec) -> list[str]:
    errors = []

    if order.order_quantity_kg <= 0:
        errors.append("Order quantity must be greater than zero.")
    if order.minimum_batch_size_kg <= 0:
        errors.append("Minimum batch size must be greater than zero.")
    if order.maximum_batch_size_kg < order.minimum_batch_size_kg:
        errors.append(
            f"Maximum batch size ({order.maximum_batch_size_kg:g} kg) must be greater than or "
            f"equal to the minimum batch size ({order.minimum_batch_size_kg:g} kg)."
        )
    if len(set(order.available_batch_sizes_kg)) != len(order.available_batch_sizes_kg):
        errors.append("Available batch sizes must not contain duplicates.")
    for size in order.available_batch_sizes_kg:
        if size < order.minimum_batch_size_kg or size > order.maximum_batch_size_kg:
            errors.append(
                f"Available batch size {size:g} kg is outside the allowed range "
                f"[{order.minimum_batch_size_kg:g}, {order.maximum_batch_size_kg:g}] kg."
            )

    if errors:
        # Bounds are already broken; a feasibility check on top would just be noise.
        return errors

    if not _is_feasible(order):
        errors.append(
            f"Order quantity {order.order_quantity_kg:g} kg cannot be divided into any valid "
            f"combination of batches between {order.minimum_batch_size_kg:g} kg and "
            f"{order.maximum_batch_size_kg:g} kg."
        )
    return errors


def _is_feasible(order: OrderSpec) -> bool:
    # A quantity is reachable with n batches iff n*min <= qty <= n*max for some
    # positive integer n, since batch sizes between min and max are unconstrained.
    min_b, max_b, qty = order.minimum_batch_size_kg, order.maximum_batch_size_kg, order.order_quantity_kg
    max_n = int(qty // min_b) + 1
    return any(n * min_b - EPSILON <= qty <= n * max_b + EPSILON for n in range(1, max_n + 1))


def validate_plan(plan: list[float], order: OrderSpec) -> list[str]:
    errors = []

    total = sum(plan)
    if abs(total - order.order_quantity_kg) > EPSILON:
        errors.append(
            f"The final batch total is {total:g} kg, but the order quantity is "
            f"{order.order_quantity_kg:g} kg."
        )

    for index, batch in enumerate(plan, start=1):
        if batch <= 0:
            errors.append(f"Batch {index} is {batch:g} kg, which must be a positive quantity.")
            continue
        if batch < order.minimum_batch_size_kg - EPSILON:
            errors.append(
                f"Batch {index} is {batch:g} kg, which is below the minimum allowed size of "
                f"{order.minimum_batch_size_kg:g} kg."
            )
        if batch > order.maximum_batch_size_kg + EPSILON:
            errors.append(
                f"Batch {index} is {batch:g} kg, which is above the maximum allowed size of "
                f"{order.maximum_batch_size_kg:g} kg."
            )

    return errors
