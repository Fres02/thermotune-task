from dataclasses import dataclass, field


@dataclass(frozen=True)
class OrderSpec:
    order_quantity_kg: float
    minimum_batch_size_kg: float
    maximum_batch_size_kg: float
    available_batch_sizes_kg: list[float] = field(default_factory=list)


@dataclass
class HistoryStats:
    # value -> fraction of the time that batch size survived unchanged from a
    # recommended suggestion into the planner's final plan.
    batch_acceptance_rates: dict[float, float] = field(default_factory=dict)
    # canonical (sorted-descending) final plan -> recency-weighted count of
    # times it was chosen for orders within a similar quantity range.
    similar_order_plan_counts: dict[tuple[float, ...], float] = field(default_factory=dict)
