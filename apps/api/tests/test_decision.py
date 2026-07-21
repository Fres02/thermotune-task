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


def test_accepting_recommendation_gives_100_percent_similarity(client):
    order = _create_order(client, "ORD-ACCEPT")
    recommended = next(s for s in order["suggestions"] if s["recommended"])

    response = client.post(
        f"/api/orders/{order['order_id']}/decision",
        json={"final_batches": recommended["batches"]},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["accepted_without_changes"] is True
    assert body["change_count"] == 0
    assert body["change_types"] == []
    assert body["similarity_score"] == 100.0


def test_invalid_total_is_rejected(client):
    order = _create_order(client, "ORD-BADSUM")

    response = client.post(
        f"/api/orders/{order['order_id']}/decision",
        json={"final_batches": [800, 800, 700]},
    )

    assert response.status_code == 422
    assert "2300" in response.json()["detail"][0]
    assert "2400" in response.json()["detail"][0]


def test_batch_below_minimum_is_rejected(client):
    order = _create_order(client, "ORD-BELOWMIN")

    response = client.post(
        f"/api/orders/{order['order_id']}/decision",
        json={"final_batches": [800, 800, 500, 300]},
    )

    assert response.status_code == 422
    assert "below the minimum" in response.json()["detail"][0]


def test_resize_is_recorded_with_reason(client):
    order = _create_order(client, "ORD-RESIZE")
    # Recommended is [800,800,800]; this resizes every batch.

    response = client.post(
        f"/api/orders/{order['order_id']}/decision",
        json={
            "final_batches": [1000, 1000, 400],
            "change_reason": "Better machine capacity",
            "comment": "Needs to fit the 1000kg dye vat run",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["accepted_without_changes"] is False
    assert body["change_count"] == 3
    assert "RESIZE" in body["change_types"]
    assert body["change_reason"] == "Better machine capacity"


def test_split_is_recorded(client):
    order = _create_order(client, "ORD-SPLIT")
    # Recommended is [800,800,800]; split one 800 into two 400s.

    response = client.post(
        f"/api/orders/{order['order_id']}/decision",
        json={"final_batches": [800, 800, 400, 400], "change_reason": "Avoid a small batch"},
    )

    assert response.status_code == 201
    body = response.json()
    assert "SPLIT" in body["change_types"]
    assert body["change_reason"] == "Avoid a small batch"


def test_invalid_change_reason_is_rejected(client):
    order = _create_order(client, "ORD-BADREASON")

    response = client.post(
        f"/api/orders/{order['order_id']}/decision",
        json={"final_batches": [800, 800, 800], "change_reason": "not a real reason"},
    )

    assert response.status_code == 422


def test_decision_persists_and_is_returned_by_get_order(client):
    order = _create_order(client, "ORD-PERSIST")

    client.post(
        f"/api/orders/{order['order_id']}/decision",
        json={"final_batches": [1000, 1000, 400], "change_reason": "Quality requirement"},
    )

    response = client.get(f"/api/orders/{order['order_id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["decision"]["order_id"] == "ORD-PERSIST"
    assert body["decision"]["change_reason"] == "Quality requirement"


def test_decision_for_unknown_order_is_404(client):
    response = client.post(
        "/api/orders/NOPE/decision",
        json={"final_batches": [800, 800, 800]},
    )
    assert response.status_code == 404
