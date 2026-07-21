from datetime import datetime, timedelta, timezone

from app.models import Order, Suggestion, UserDecision
from app.services.history import all_plan_counts, batch_acceptance_stats, similar_order_plan_counts
from app.services.score import MAX_HISTORICAL_BONUS, historical_score
from app.services.types import HistoryStats, OrderSpec

DEFAULT_ORDER = {
    "order_quantity_kg": 2400,
    "available_batch_sizes_kg": [500, 800, 1000],
    "minimum_batch_size_kg": 400,
    "maximum_batch_size_kg": 1000,
}


def _create_order(client, order_id, **overrides):
    payload = {"order_id": order_id, **DEFAULT_ORDER, **overrides}
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _score_of(order_response, batches):
    return next(s["score"] for s in order_response["suggestions"] if s["batches"] == batches)


def _seed_decision(
    db_session,
    *,
    order_id,
    order_quantity_kg,
    initial_batches,
    final_batches,
    accepted_without_changes,
    created_at=None,
):
    order = Order(
        order_id=order_id,
        order_quantity_kg=order_quantity_kg,
        available_batch_sizes_kg=[],
        minimum_batch_size_kg=100,
        maximum_batch_size_kg=2000,
        status="completed",
    )
    suggestion = Suggestion(
        batches=initial_batches, score=0, rank=1, explanation="seed", recommended=True
    )
    order.suggestions.append(suggestion)
    db_session.add(order)
    db_session.flush()  # assigns ids so the decision below can reference them

    decision = UserDecision(
        order_id=order.id,
        suggestion_id=suggestion.id,
        final_batches=final_batches,
        accepted_without_changes=accepted_without_changes,
        change_count=0 if accepted_without_changes else 1,
        change_types=[] if accepted_without_changes else ["RESIZE"],
        similarity_score=100.0 if accepted_without_changes else 50.0,
    )
    if created_at is not None:
        decision.created_at = created_at
    db_session.add(decision)
    db_session.commit()
    return decision


# --- pure service-level tests (db_session, no HTTP) -------------------------------------


def test_batch_acceptance_stats_measures_survival_not_just_occurrence(db_session):
    # 800 is offered (present in the initial plan) and kept in one decision, offered
    # again but not kept at all in another.
    _seed_decision(
        db_session, order_id="S1", order_quantity_kg=2400,
        initial_batches=[800, 800, 800], final_batches=[800, 800, 800],
        accepted_without_changes=True,
    )
    _seed_decision(
        db_session, order_id="S2", order_quantity_kg=2400,
        initial_batches=[800, 800, 800], final_batches=[1000, 1000, 400],
        accepted_without_changes=False,
    )

    rates = batch_acceptance_stats(db_session)

    assert 1000 not in rates  # never appeared in an initial/recommended plan, only user-introduced
    assert abs(rates[800] - 0.5) < 0.01  # offered 6 times total, kept 3 times


def test_similar_order_plan_counts_only_includes_orders_within_range(db_session):
    _seed_decision(
        db_session, order_id="S1", order_quantity_kg=2400,
        initial_batches=[800, 800, 800], final_batches=[1000, 1000, 400],
        accepted_without_changes=False,
    )
    _seed_decision(
        db_session, order_id="S2", order_quantity_kg=5000,
        initial_batches=[800, 800, 800], final_batches=[1000, 1000, 400],
        accepted_without_changes=False,
    )

    counts = similar_order_plan_counts(db_session, order_quantity_kg=2400, range_pct=0.10)

    key = (1000.0, 1000.0, 400.0)
    assert abs(counts[key] - 1.0) < 0.01  # only the 2400kg order is within +-10%; 5000kg is not


def test_all_plan_counts_includes_every_decision_regardless_of_order_size(db_session):
    _seed_decision(
        db_session, order_id="S1", order_quantity_kg=2400,
        initial_batches=[800, 800, 800], final_batches=[1000, 1000, 400],
        accepted_without_changes=False,
    )
    _seed_decision(
        db_session, order_id="S2", order_quantity_kg=5000,
        initial_batches=[800, 800, 800], final_batches=[1000, 1000, 400],
        accepted_without_changes=False,
    )

    counts = all_plan_counts(db_session)

    key = (1000.0, 1000.0, 400.0)
    assert abs(counts[key] - 2.0) < 0.02  # both decisions count, regardless of order size


def test_recency_weighting_favours_recent_decisions(db_session):
    now = datetime.now(timezone.utc)
    _seed_decision(
        db_session, order_id="OLD", order_quantity_kg=2400,
        initial_batches=[800, 800, 800], final_batches=[1000, 1000, 400],
        accepted_without_changes=False, created_at=now - timedelta(days=60),  # two half-lives ago
    )
    _seed_decision(
        db_session, order_id="RECENT", order_quantity_kg=2400,
        initial_batches=[800, 800, 800], final_batches=[1000, 1000, 400],
        accepted_without_changes=False, created_at=now,
    )

    counts = all_plan_counts(db_session, now=now)
    key = (1000.0, 1000.0, 400.0)
    # ~1.0 (recent) + ~0.25 (60 days old at a 30-day half-life) = ~1.25, not 2.0.
    assert 1.0 < counts[key] < 1.5


# --- score.py integration: the bonus is capped and never negative ---------------------


def test_historical_score_is_capped_even_with_extreme_history():
    order = OrderSpec(
        order_quantity_kg=2400, minimum_batch_size_kg=400,
        maximum_batch_size_kg=1000, available_batch_sizes_kg=[800],
    )
    stats = HistoryStats(
        batch_acceptance_rates={800: 1.0},
        similar_order_plan_counts={(800.0, 800.0, 800.0): 1000.0},
    )

    value, reason, is_positive = historical_score([800, 800, 800], order, stats)

    assert value == MAX_HISTORICAL_BONUS
    assert is_positive is True
    assert reason is not None


def test_historical_score_is_zero_with_no_history():
    order = OrderSpec(order_quantity_kg=2400, minimum_batch_size_kg=400, maximum_batch_size_kg=1000)
    value, reason, is_positive = historical_score([800, 800, 800], order, None)
    assert value == 0
    assert reason is None


# --- API-level: measurable shift, but never overtakes or bypasses validation ------------


def test_historical_bonus_measurably_shifts_ranking_without_overtaking(client):
    baseline = _create_order(client, "ORD-BASELINE")
    baseline_score = _score_of(baseline, [1000.0, 1000.0, 400.0])

    for i in range(3):
        seed = _create_order(client, f"ORD-SEED-{i}")
        client.post(
            f"/api/orders/{seed['order_id']}/decision",
            json={"final_batches": [1000, 1000, 400], "change_reason": "Better machine capacity"},
        )

    after = _create_order(client, "ORD-AFTER")
    after_score = _score_of(after, [1000.0, 1000.0, 400.0])
    recommended = next(s for s in after["suggestions"] if s["recommended"])

    assert after_score > baseline_score  # measurable shift upward
    assert recommended["batches"] == [800.0, 800.0, 800.0]  # still never overtaken


def test_historical_bonus_never_lets_an_invalid_plan_through(client):
    order = _create_order(client, "ORD-HIST-INVALID")

    for i in range(5):
        seed = _create_order(client, f"ORD-HIST-SEED-{i}")
        client.post(
            f"/api/orders/{seed['order_id']}/decision",
            json={"final_batches": [1000, 1000, 400]},
        )

    response = client.post(
        f"/api/orders/{order['order_id']}/decision",
        json={"final_batches": [1000, 1000, 300]},  # sums to 2300, not 2400 -- still invalid
    )

    assert response.status_code == 422
