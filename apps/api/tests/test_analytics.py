import pytest

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


def test_summary_is_zeroed_out_with_no_decisions(client):
    response = client.get("/api/analytics/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_completed_orders"] == 0
    assert body["acceptance_rate"] == 0.0
    assert body["average_changes"] == 0.0
    assert body["most_selected_batch_size"] is None
    assert body["most_common_change_reason"] is None
    assert body["average_similarity_score"] == 0.0


def test_summary_matches_hand_computed_values(client):
    # 1 accepted unchanged, 3 resized to the same alternate plan.
    order1 = _create_order(client, "ORD-A1")
    client.post(
        f"/api/orders/{order1['order_id']}/decision",
        json={"final_batches": [800, 800, 800]},
    )

    for i in range(3):
        order = _create_order(client, f"ORD-A-RESIZE-{i}")
        client.post(
            f"/api/orders/{order['order_id']}/decision",
            json={"final_batches": [1000, 1000, 400], "change_reason": "Better machine capacity"},
        )

    response = client.get("/api/analytics/summary")
    body = response.json()

    assert body["total_completed_orders"] == 4
    assert body["acceptance_rate"] == 25.0  # 1 accepted / 4 total x 100
    assert body["average_changes"] == pytest.approx((0 + 3 + 3 + 3) / 4)
    assert body["most_selected_batch_size"] == 1000.0  # appears 6 times vs. 800's 3
    assert body["most_common_change_reason"] == "Better machine capacity"


def test_preferences_reflects_seeded_history(client):
    order1 = _create_order(client, "ORD-P1")
    client.post(
        f"/api/orders/{order1['order_id']}/decision",
        json={"final_batches": [800, 800, 800]},
    )

    order2 = _create_order(client, "ORD-P2")
    client.post(
        f"/api/orders/{order2['order_id']}/decision",
        json={"final_batches": [1000, 1000, 400]},
    )

    response = client.get("/api/analytics/preferences")
    body = response.json()

    assert "800" in body["batch_acceptance_rates"]
    assert "800 + 800 + 800" in body["similar_order_patterns"]
    assert "1000 + 1000 + 400" in body["similar_order_patterns"]
