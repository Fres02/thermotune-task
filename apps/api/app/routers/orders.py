from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Order, Suggestion, UserDecision
from app.schemas import (
    DecisionRequest,
    DecisionResponse,
    OrderCreateRequest,
    OrderDetailResponse,
    OrderResponse,
    SuggestionOut,
)
from app.services.change_detect import count_changed_batches, detect_change_types
from app.services.generate import generate_plans
from app.services.history import build_history_stats
from app.services.score import build_explanation, score_plan
from app.services.similarity import compute_similarity
from app.services.types import OrderSpec
from app.services.validate import validate_order_input, validate_plan

router = APIRouter(prefix="/api/orders", tags=["orders"])

# generate_plans can legitimately find dozens of valid combinations for a
# given order; only the highest-scoring ones are worth ranking, showing, and
# persisting. Ranking still considers the full candidate pool -- this only
# trims what happens after scoring.
MAX_PERSISTED_SUGGESTIONS = 20


def _to_order_spec(payload: OrderCreateRequest) -> OrderSpec:
    return OrderSpec(
        order_quantity_kg=payload.order_quantity_kg,
        minimum_batch_size_kg=payload.minimum_batch_size_kg,
        maximum_batch_size_kg=payload.maximum_batch_size_kg,
        available_batch_sizes_kg=payload.available_batch_sizes_kg,
    )


def _order_spec_from_row(order_row: Order) -> OrderSpec:
    return OrderSpec(
        order_quantity_kg=order_row.order_quantity_kg,
        minimum_batch_size_kg=order_row.minimum_batch_size_kg,
        maximum_batch_size_kg=order_row.maximum_batch_size_kg,
        available_batch_sizes_kg=order_row.available_batch_sizes_kg,
    )


def _next_order_id(db: Session) -> str:
    # Sequential ORD-NNN, starting from the current order count. Skips ahead
    # if that candidate is already taken (e.g. by an earlier manually-named
    # order) rather than colliding with it.
    candidate_num = db.scalar(select(func.count()).select_from(Order)) + 1
    while True:
        candidate = f"ORD-{candidate_num:03d}"
        if not db.scalar(select(Order.id).where(Order.order_id == candidate)):
            return candidate
        candidate_num += 1


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(payload: OrderCreateRequest, db: Session = Depends(get_db)):
    order_id = payload.order_id or _next_order_id(db)

    existing = db.scalar(select(Order).where(Order.order_id == order_id))
    if existing:
        raise HTTPException(status_code=409, detail=[f"Order '{order_id}' already exists."])

    order_spec = _to_order_spec(payload)
    input_errors = validate_order_input(order_spec)
    if input_errors:
        raise HTTPException(status_code=422, detail=input_errors)

    plans = generate_plans(
        order_spec.order_quantity_kg,
        order_spec.available_batch_sizes_kg,
        order_spec.minimum_batch_size_kg,
        order_spec.maximum_batch_size_kg,
    )
    if not plans:
        raise HTTPException(
            status_code=422,
            detail=["No valid batch plan could be generated for this order."],
        )

    history_stats = build_history_stats(db, order_spec.order_quantity_kg)
    scored = [(plan, score_plan(plan, order_spec, history_stats)) for plan in plans]
    scored.sort(key=lambda item: item[1].total, reverse=True)
    scored = scored[:MAX_PERSISTED_SUGGESTIONS]

    order_row = Order(
        order_id=order_id,
        order_quantity_kg=payload.order_quantity_kg,
        available_batch_sizes_kg=payload.available_batch_sizes_kg,
        minimum_batch_size_kg=payload.minimum_batch_size_kg,
        maximum_batch_size_kg=payload.maximum_batch_size_kg,
        status="suggested",
    )

    for rank, (plan, result) in enumerate(scored, start=1):
        recommended = rank == 1
        order_row.suggestions.append(
            Suggestion(
                batches=plan,
                score=result.total,
                rank=rank,
                explanation=build_explanation(result, recommended=recommended),
                recommended=recommended,
                historically_preferred=result.historically_preferred,
            )
        )

    db.add(order_row)
    db.commit()
    db.refresh(order_row)

    return OrderResponse(
        order_id=order_row.order_id,
        suggestions=[SuggestionOut.model_validate(s) for s in order_row.suggestions],
    )


@router.get("/{order_id}", response_model=OrderDetailResponse)
def get_order(order_id: str, db: Session = Depends(get_db)):
    order_row = db.scalar(select(Order).where(Order.order_id == order_id))
    if not order_row:
        raise HTTPException(status_code=404, detail=[f"Order '{order_id}' not found."])

    suggestions = sorted(order_row.suggestions, key=lambda s: s.rank)
    latest_decision = order_row.decisions[-1] if order_row.decisions else None
    decision = (
        DecisionResponse(
            order_id=order_row.order_id,  # the external id, not latest_decision's internal FK
            final_batches=latest_decision.final_batches,
            accepted_without_changes=latest_decision.accepted_without_changes,
            change_count=latest_decision.change_count,
            change_types=latest_decision.change_types,
            change_reason=latest_decision.change_reason,
            similarity_score=latest_decision.similarity_score,
            created_at=latest_decision.created_at,
        )
        if latest_decision
        else None
    )

    return OrderDetailResponse(
        order_id=order_row.order_id,
        order_quantity_kg=order_row.order_quantity_kg,
        status=order_row.status,
        suggestions=[SuggestionOut.model_validate(s) for s in suggestions],
        decision=decision,
    )


@router.post("/{order_id}/decision", response_model=DecisionResponse, status_code=201)
def submit_decision(order_id: str, payload: DecisionRequest, db: Session = Depends(get_db)):
    order_row = db.scalar(select(Order).where(Order.order_id == order_id))
    if not order_row:
        raise HTTPException(status_code=404, detail=[f"Order '{order_id}' not found."])

    recommended = next((s for s in order_row.suggestions if s.recommended), None)
    if not recommended:
        raise HTTPException(
            status_code=422,
            detail=["Order has no recommended suggestion to compare the decision against."],
        )

    plan_errors = validate_plan(payload.final_batches, _order_spec_from_row(order_row))
    if plan_errors:
        raise HTTPException(status_code=422, detail=plan_errors)

    initial_plan = recommended.batches
    final_plan = payload.final_batches

    change_types = detect_change_types(initial_plan, final_plan)
    accepted_without_changes = change_types == ["ACCEPTED"]
    change_count = 0 if accepted_without_changes else count_changed_batches(initial_plan, final_plan)
    similarity = compute_similarity(initial_plan, final_plan, order_row.order_quantity_kg)

    decision_row = UserDecision(
        order_id=order_row.id,
        suggestion_id=recommended.id,
        final_batches=final_plan,
        accepted_without_changes=accepted_without_changes,
        change_count=change_count,
        change_types=[] if accepted_without_changes else change_types,
        change_reason=payload.change_reason.value if payload.change_reason else None,
        comment=payload.comment,
        similarity_score=similarity,
    )

    order_row.status = "completed"
    db.add(decision_row)
    db.commit()
    db.refresh(decision_row)

    return DecisionResponse(
        order_id=order_row.order_id,
        final_batches=decision_row.final_batches,
        accepted_without_changes=decision_row.accepted_without_changes,
        change_count=decision_row.change_count,
        change_types=decision_row.change_types,
        change_reason=decision_row.change_reason,
        similarity_score=decision_row.similarity_score,
        created_at=decision_row.created_at,
    )
