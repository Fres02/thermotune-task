from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UserDecision
from app.schemas import AnalyticsSummaryResponse, PreferencesResponse
from app.services.history import all_plan_counts, batch_acceptance_stats

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

TOP_PATTERNS_LIMIT = 10


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_summary(db: Session = Depends(get_db)):
    decisions = db.scalars(select(UserDecision)).all()
    total = len(decisions)

    if total == 0:
        return AnalyticsSummaryResponse(
            total_completed_orders=0,
            acceptance_rate=0.0,
            average_changes=0.0,
            most_selected_batch_size=None,
            most_common_change_reason=None,
            average_similarity_score=0.0,
        )

    accepted_count = sum(1 for decision in decisions if decision.accepted_without_changes)
    total_changes = sum(decision.change_count for decision in decisions)
    total_similarity = sum(decision.similarity_score for decision in decisions)

    batch_counter: Counter[float] = Counter()
    for decision in decisions:
        batch_counter.update(decision.final_batches)
    reason_counter = Counter(decision.change_reason for decision in decisions if decision.change_reason)

    return AnalyticsSummaryResponse(
        total_completed_orders=total,
        acceptance_rate=accepted_count / total * 100,
        average_changes=total_changes / total,
        most_selected_batch_size=batch_counter.most_common(1)[0][0] if batch_counter else None,
        most_common_change_reason=reason_counter.most_common(1)[0][0] if reason_counter else None,
        average_similarity_score=total_similarity / total,
    )


@router.get("/preferences", response_model=PreferencesResponse)
def get_preferences(db: Session = Depends(get_db)):
    acceptance_rates = batch_acceptance_stats(db)
    plan_counts = all_plan_counts(db)

    top_patterns = sorted(plan_counts.items(), key=lambda item: item[1], reverse=True)[:TOP_PATTERNS_LIMIT]

    return PreferencesResponse(
        batch_acceptance_rates={f"{size:g}": round(rate, 4) for size, rate in acceptance_rates.items()},
        similar_order_patterns={
            " + ".join(f"{batch:g}" for batch in plan): round(weight, 2) for plan, weight in top_patterns
        },
    )
