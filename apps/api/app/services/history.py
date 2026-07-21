from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Order, UserDecision
from app.services.types import HistoryStats

DEFAULT_SIMILAR_ORDER_RANGE_PCT = 0.10
RECENCY_HALF_LIFE_DAYS = 30  # a decision from 30 days ago counts half as much as one from today


def _recency_weight(created_at: datetime, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (now - created_at).total_seconds() / 86400)
    return 0.5 ** (age_days / RECENCY_HALF_LIFE_DAYS)


def batch_acceptance_stats(db: Session, now: datetime | None = None) -> dict[float, float]:
    decisions = db.scalars(select(UserDecision)).all()

    offered: dict[float, float] = defaultdict(float)
    kept: dict[float, float] = defaultdict(float)

    for decision in decisions:
        weight = _recency_weight(decision.created_at, now)
        initial_counts = _counts(decision.suggestion.batches)
        final_counts = _counts(decision.final_batches)
        for value, offered_count in initial_counts.items():
            offered[value] += offered_count * weight
            # A batch size can only be credited as "kept" up to how many of it
            # actually remain in the final plan -- never more than were offered.
            kept[value] += min(offered_count, final_counts.get(value, 0)) * weight

    return {value: kept[value] / offered[value] for value in offered if offered[value] > 0}


def similar_order_plan_counts(
    db: Session,
    order_quantity_kg: float,
    range_pct: float = DEFAULT_SIMILAR_ORDER_RANGE_PCT,
    now: datetime | None = None,
) -> dict[tuple[float, ...], float]:
    low = order_quantity_kg * (1 - range_pct)
    high = order_quantity_kg * (1 + range_pct)

    decisions = db.scalars(
        select(UserDecision)
        .join(Order, UserDecision.order_id == Order.id)
        .where(Order.order_quantity_kg.between(low, high))
    ).all()

    counts: dict[tuple[float, ...], float] = defaultdict(float)
    for decision in decisions:
        weight = _recency_weight(decision.created_at, now)
        canonical = tuple(sorted(decision.final_batches, reverse=True))
        counts[canonical] += weight

    return dict(counts)


def all_plan_counts(db: Session, now: datetime | None = None) -> dict[tuple[float, ...], float]:
    # Same recency-weighted counting as similar_order_plan_counts, but across
    # every decision -- used for the dashboard's order-agnostic "commonly
    # accepted plans" view rather than for ranking a specific new order.
    decisions = db.scalars(select(UserDecision)).all()

    counts: dict[tuple[float, ...], float] = defaultdict(float)
    for decision in decisions:
        weight = _recency_weight(decision.created_at, now)
        canonical = tuple(sorted(decision.final_batches, reverse=True))
        counts[canonical] += weight

    return dict(counts)


def build_history_stats(
    db: Session,
    order_quantity_kg: float,
    range_pct: float = DEFAULT_SIMILAR_ORDER_RANGE_PCT,
) -> HistoryStats:
    return HistoryStats(
        batch_acceptance_rates=batch_acceptance_stats(db),
        similar_order_plan_counts=similar_order_plan_counts(db, order_quantity_kg, range_pct),
    )


def _counts(values: list[float]) -> dict[float, int]:
    counts: dict[float, int] = defaultdict(int)
    for value in values:
        counts[value] += 1
    return counts
