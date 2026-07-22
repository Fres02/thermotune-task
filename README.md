# TexTune Batch Split Suggestion Engine

Splits a production order into valid batches, ranks the options, explains the
recommendation, lets a planner edit it, and learns from what planners actually
keep.

## Live Demo

- Frontend: https://thermotune-task.vercel.app
- API docs: https://textune-api.onrender.com/docs

## Tech Stack

FastAPI + SQLAlchemy (SQLite locally, Postgres in production) for the backend,
React + Vite for the frontend, Docker Compose for local development.

## Setup

```bash
git clone https://github.com/Fres02/thermotune-task.git
cd thermotune-task
docker compose up --build
```

- Frontend: http://localhost:5173
- API + docs: http://localhost:8000/docs

To use Postgres instead of the default SQLite:

```bash
docker compose --profile postgres up --build
```

## Running Tests

```bash
cd apps/api
pip install -r requirements.txt
pytest
```

42 tests covering generation, ranking, similarity, validation, decisions,
analytics, and historical learning.

## Sample Data

See `sample-data/` for example order and decision payloads with documented
expected results, usable directly with `curl`.

## Approach

An order is split into candidate batch plans with a backtracking search over
preferred sizes plus the min/max/step range, pruning invalid branches and
deduplicating equivalent plans. Each valid plan is scored on preferred-size
match, equal-sized batches, avoiding near-minimum remainders, and batch count,
plus a capped historical bonus. The top-scoring plan is recommended with a
plain-language explanation built from the same scoring factors. A planner can
accept it as it is or edit it (add, remove, split, merge, resize) through the
batch editor, which validates live and is re-validated by the server before a
decision is saved.

## Assumptions

- Batch quantities are whole kilograms.
- Available batch sizes are preferences, not hard restrictions; the generator
  also uses min/max/step-derived sizes to fill in gaps.
- Historical learning only adjusts ranking; it never bypasses validation.
- User preference is inferred only from completed decisions.

## Measuring Suggestion Quality

`GET /api/analytics/summary` reports acceptance rate, average changes per
order, most-selected batch size, most common change reason, and average
similarity score. Similarity between the initial and final plan blends how
much quantity moved (80%) with whether the batch count changed (20%),
clamped to 0-100%.

## How Historical Feedback Improves Future Suggestions

Two rule-based signals feed into ranking, both capped and additive so they
nudge but never override validation: how often a batch size survives
unchanged from a recommendation into a final plan, and how often a specific
plan has been chosen for orders of a similar quantity (recency-weighted).
`GET /api/analytics/preferences` exposes both for transparency.

## Future Improvements

- Train a model on accepted/modified decisions once enough data exists.
- Product and machine-specific preferences.
- Recency-weighted history tuning, exportable reports, drag-and-drop editing.

