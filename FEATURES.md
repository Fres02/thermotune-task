# FEATURES.md

## Phase 0: Scaffold

- Repo layout: apps/api, apps/web, sample-data, screenshots, tests
- FastAPI app boots, /docs loads
- SQLAlchemy engine, session, and DB dependency wired up
- Vite + React app boots and can reach the API
- docker-compose.yml for api, web, and optional postgres

## Phase 1: Data model

- Order table: order_id, order_quantity_kg, minimum_batch_size_kg, maximum_batch_size_kg, status, created_at
- Suggestion table: order_id, batches, score, rank, explanation, explanation_polished, recommended
- UserDecision table: order_id, suggestion_id, final_batches, accepted_without_changes, change_count, change_types, change_reason, comment, similarity_score, created_at
- Pydantic request and response schemas matching the assignment's example payloads
- Tables auto created on startup

## Phase 2: Core services

- validate_plan(plan, order): checks sum, minimum, maximum, positive values, in that order
- validate_order_input(order): checks quantity, min, max, duplicate sizes, feasibility
- generate_plans(order_qty, available_sizes, min_size, max_size, step, node_limit): backtracking search with pruning, canonical dedup, and a node cap
- score_plan sub functions: preferred_size_score, equal_size_score, small_batch_penalty, extra_batch_penalty
- score_plan(plan, order, history_stats): combines sub scores into a total plus a reasons list
- build_explanation(reasons): deterministic sentence built from the reasons list
- compute_similarity(initial, final, order_qty): quantity difference and structure similarity blended and clamped to 0 to 100
- detect_change_types(initial, final): classifies accepted, resize, split, merge, add, remove, replaced

## Phase 3: Order and suggestion API

- POST /api/orders: validate input, generate plans, score and rank them, persist order and suggestions, return the ranked list
- GET /api/orders/{order_id}: order, its suggestions, and its decision if one exists
- Clear rejection message when no valid plan exists for the given inputs

## Phase 4: Explanation polish

- polish_explanation(sentence, reasons): optional Gemini call constrained to rewording only, with a timeout
- Falls back to the deterministic sentence on any failure or missing API key
- Only the top ranked suggestion gets polished
- GEMINI_API_KEY read from environment, app works fully without it

## Phase 5: User decision and feedback capture

- POST /api/orders/{order_id}/decision: validate the final plan first, then detect change types and compute similarity against the recommendation
- accepted_without_changes derived by comparing sorted final and initial plans
- Change reason options: better machine capacity, avoid a small batch, prefer equal batch sizes, quality requirement, delivery urgency, other, plus a free text comment
- Invalid decisions rejected with the specific rule that failed

## Phase 6: Historical learning

- batch_acceptance_stats(db): how often each batch size survives untouched versus how often it was offered
- similar_order_bonus(db, order_qty, range_pct): looks up decisions from orders within a configurable quantity range
- Historical score wired into score_plan as a capped, additive bonus that never overrides validation
- Recency weighting so recent decisions count more than old ones

## Phase 7: Analytics API

- GET /api/analytics/summary: acceptance rate, average changes per order, most frequent batch size, most common change reason, average similarity score
- GET /api/analytics/preferences: exposes the same numbers history.py uses internally, for dashboard transparency

## Phase 8: Frontend

- Lightweight client side mirror of validate_plan for instant feedback while editing
- OrderForm: order id, quantity, available sizes, min, max
- SuggestionsList: ranked cards, top suggestion highlighted, score and explanation shown
- BatchEditor: add, remove, split, merge, and resize batches, live running total versus order quantity, submit disabled until valid
- FeedbackForm: reason dropdown, comment, confirm, surfaces server validation errors
- Dashboard: acceptance rate, average changes, most selected batch size, most common reason, average similarity
- Drag and drop batch editing
- Charts on the dashboard instead of plain number cards

## Phase 9: Testing

- Generation tests: valid plans for 2400kg, sums and bounds always respected, no duplicates, known invalid combinations never appear
- Similarity tests: reproduces the worked example by hand, score always stays within 0 to 100
- Decision tests: accepting unchanged gives 100 percent similarity, invalid totals and undersized batches are rejected, split and resize are recorded correctly
- Analytics tests: acceptance rate and average changes match hand computed values, most common batch size identified correctly
- History tests: historical bonus shifts ranking after seeding repeated acceptances, but never overrides a validation failure

## Phase 10: Deliverables

- Sample order payloads in sample-data, including an impossible case
- README with setup, run commands, and a worked example
- AI_USAGE.md filled in as the project is built
- Screenshots or a short demo video of the main screens
- Short write up covering approach, assumptions, generation and ranking, similarity formula, historical feedback usage, and future improvements
- Finished docker-compose setup

