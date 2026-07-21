import math
from dataclasses import dataclass, field

from app.services.types import HistoryStats, OrderSpec

PREFERRED_SIZE_POINTS = 20
EQUAL_SIZE_POINTS = 25
SMALL_BATCH_PENALTY = 20
EXTRA_BATCH_PENALTY = 5
SMALL_BATCH_MARGIN_RATIO = 0.10  # a batch within 10% of the minimum counts as "near minimum"

MAX_HISTORICAL_BONUS = 30  # historical score can never outweigh a validation-sized penalty
ACCEPTANCE_RATE_POINTS = 10  # max contribution from how often a plan's batch sizes are kept
SIMILAR_ORDER_POINTS_PER_MATCH = 5
SIMILAR_ORDER_MAX_POINTS = 20


@dataclass
class ScoreResult:
    total: float
    positive_reasons: list[str] = field(default_factory=list)
    negative_reasons: list[str] = field(default_factory=list)
    historically_preferred: bool = False


def preferred_size_score(plan: list[float], order: OrderSpec) -> tuple[float, str | None, bool]:
    matches = sum(1 for batch in plan if batch in order.available_batch_sizes_kg)
    if matches == 0:
        return 0, None, True
    return matches * PREFERRED_SIZE_POINTS, "matches a preferred batch size", True


def equal_size_score(plan: list[float], order: OrderSpec) -> tuple[float, str | None, bool]:
    if len(plan) > 1 and len(set(plan)) == 1:
        return EQUAL_SIZE_POINTS, "uses equal-sized batches", True
    return 0, None, True


def small_batch_check(plan: list[float], order: OrderSpec) -> tuple[float, str | None, bool]:
    threshold = order.minimum_batch_size_kg * (1 + SMALL_BATCH_MARGIN_RATIO)
    if any(batch <= threshold for batch in plan):
        return -SMALL_BATCH_PENALTY, "contains a minimum-sized remainder batch", False
    return 0, "avoids a small remaining batch", True


def extra_batch_penalty(plan: list[float], order: OrderSpec) -> tuple[float, str | None, bool]:
    minimal_count = _minimal_batch_count(order)
    extra = max(0, len(plan) - minimal_count)
    if extra == 0:
        return 0, None, True
    return -extra * EXTRA_BATCH_PENALTY, "uses more batches than necessary", False


def _minimal_batch_count(order: OrderSpec) -> int:
    if order.maximum_batch_size_kg <= 0:
        return 1
    return max(1, math.ceil(order.order_quantity_kg / order.maximum_batch_size_kg))


def historical_score(
    plan: list[float], order: OrderSpec, history_stats: HistoryStats | None
) -> tuple[float, str | None, bool]:
    # Purely additive and capped: historical data can nudge ranking toward
    # what planners have kept before, but can never outweigh (let alone
    # bypass) the validation-sized penalties above.
    if not history_stats or not plan:
        return 0, None, True

    acceptance_rates = history_stats.batch_acceptance_rates
    average_rate = sum(acceptance_rates.get(batch, 0.0) for batch in plan) / len(plan)
    acceptance_component = average_rate * ACCEPTANCE_RATE_POINTS

    canonical = tuple(sorted(plan, reverse=True))
    match_weight = history_stats.similar_order_plan_counts.get(canonical, 0.0)
    similar_order_component = min(
        match_weight * SIMILAR_ORDER_POINTS_PER_MATCH, SIMILAR_ORDER_MAX_POINTS
    )

    total = min(acceptance_component + similar_order_component, MAX_HISTORICAL_BONUS)
    if total <= 0:
        return 0, None, True
    return total, "matches a commonly accepted pattern", True


def score_plan(
    plan: list[float], order: OrderSpec, history_stats: HistoryStats | None = None
) -> ScoreResult:
    historical_value, historical_reason, historical_is_positive = historical_score(
        plan, order, history_stats
    )
    contributions = [
        preferred_size_score(plan, order),
        equal_size_score(plan, order),
        small_batch_check(plan, order),
        extra_batch_penalty(plan, order),
        (historical_value, historical_reason, historical_is_positive),
    ]

    total = sum(value for value, _, _ in contributions)
    positive_reasons = [reason for _, reason, is_positive in contributions if reason and is_positive]
    negative_reasons = [reason for _, reason, is_positive in contributions if reason and not is_positive]

    return ScoreResult(
        total=total,
        positive_reasons=positive_reasons,
        negative_reasons=negative_reasons,
        historically_preferred=historical_value > 0,
    )


def _join(phrases: list[str]) -> str:
    if not phrases:
        return ""
    if len(phrases) == 1:
        return phrases[0]
    return ", ".join(phrases[:-1]) + ", and " + phrases[-1]


def build_explanation(result: ScoreResult, recommended: bool = False) -> str:
    positive = _join(result.positive_reasons)
    negative = _join(result.negative_reasons)

    if recommended:
        if positive and negative:
            return f"This plan is recommended because it {positive}, but {negative}."
        if positive:
            return f"This plan is recommended because it {positive}."
        if negative:
            return f"This plan is recommended, but it {negative}."
        return "This plan is recommended because it meets all requirements."

    if positive and negative:
        return f"{positive[0].upper()}{positive[1:]}, but {negative}."
    if positive:
        return f"{positive[0].upper()}{positive[1:]}."
    if negative:
        return f"Valid, but {negative}."
    return "Meets all requirements."
