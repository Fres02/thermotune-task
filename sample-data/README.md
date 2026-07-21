# Sample data

Example payloads for exercising the API directly, without going through the UI.
Every scenario below was run against the live API before being written here, so
the expected results are observed behavior, not predictions.

## Orders (`orders/`)

POST these to `http://localhost:8000/api/orders`:

```bash
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d @sample-data/orders/01-standard-example.json
```

| File | Scenario | Expected result |
|---|---|---|
| `01-standard-example.json` | The assignment's own example (§2): 2400kg, batch sizes 400-1000kg | 20 ranked suggestions (capped from a larger valid pool), recommended plan `[800, 800, 800]` |
| `02-impossible-order.json` | 500kg order, minimum batch 600kg (§13's own example) | `422`, `"Order quantity 500 kg cannot be divided into any valid combination of batches between 600 kg and 1000 kg."` |
| `03-no-preferred-sizes.json` | 9000kg order, no preferred batch sizes at all | Generator falls back entirely to min/max/step-derived candidates |
| `04-tight-batch-range.json` | 3000kg order, batch sizes constrained to 950-1000kg | Very few valid combinations -- demonstrates the search still finds them despite the narrow range |
| `05-with-optional-fields.json` | Includes `machine_capacity_kg`, `delivery_priority`, `product_type`, `planner_id` from §2's optional fields | Accepted and stored; not yet used in ranking or historical learning (documented limitation, see main README) |

`order_id` is optional on every payload -- omit it (as in `03`-`05` if you remove
that key) to get a server-assigned sequential id instead.

## Decisions (`decisions/`)

POST these to `http://localhost:8000/api/orders/{order_id}/decision`, after creating
an order from `01-standard-example.json` (or any order with the same quantity/bounds
so the recommended plan is `[800, 800, 800]`):

```bash
curl -X POST http://localhost:8000/api/orders/ORD-001/decision \
  -H "Content-Type: application/json" \
  -d @sample-data/decisions/01-accept-unchanged.json
```

| File | Scenario | Expected result |
|---|---|---|
| `01-accept-unchanged.json` | Keeps the recommended `[800,800,800]` exactly | `accepted_without_changes: true`, `change_count: 0`, `similarity_score: 100.0` |
| `02-resize-and-replace.json` | Changes to `[1000,1000,400]` | `change_types: ["RESIZE", "REPLACED"]`, `change_count: 3`, `similarity_score: 86.67` -- matches the assignment's own §6.4 worked example |
| `03-split-a-batch.json` | Changes to `[800,800,400,400]` (one 800kg batch split in two) | `change_types: ["SPLIT"]` |
| `04-invalid-wrong-total.json` | Sums to 2300kg instead of 2400kg | `422`, `"The final batch total is 2300 kg, but the order quantity is 2400 kg."` |
