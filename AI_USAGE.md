# AI Usage

## Tools Used

- Claude (Anthropic, Sonnet 5) and ChatGPT - used for frontend development (React/Vite UI), test case generation (the automated pytest suite), and sample data verification (confirming sample payloads produce the documented results against the live API).

## Where/How It Was Used

- Frontend development: building the React components (OrderForm, SuggestionsList, BatchEditor, FeedbackForm, Dashboard), the API client layer, and styling.
- Test case generation: writing the pytest suite (test_generate.py, test_similarity.py, test_change_detect.py, test_decision.py, test_analytics.py, test_history.py), including the fixtures for an isolated in-memory test database.
- Sample data verification: creating the example payloads in sample-data/ and confirming each one produces the documented result (correct scores, error messages, change types) against the live running API before writing them down.
- Debugging confirmation: used to diagnose and confirm the root cause of real issues hit during development, including a Vite file-watcher failure under Docker Desktop on Windows (bind-mount fs events not propagating), a Postgres startup race condition in Docker Compose, an internal-UUID leak in one API response field, and the Render deployment failure caused by the free-tier database limit.

## Key Prompts/Conversations

1. "I'm intentionally not using ML for the historical learning loop right now, the dataset is too small and it would compromise explainability of the scoring. Explain how I should approach introducing ML later, once enough decision data has accumulated."

2. "Explain how to modify the scoring system I built so new ranking factors can be added without breaking the existing rules."

## Accepted Suggestions

- Separating batch-plan generation and ranking into independent, framework-free service modules (generate.py, score.py) so each could be unit-tested in isolation.
- Capping the number of persisted/returned suggestions to the top 20 by score after ranking, instead of returning every valid combination found.
- Adding a distinct historically_preferred flag to each suggestion instead of relying on prose text, so historical influence on ranking is a visible, structured signal in the UI rather than buried in a sentence.
- Enabling Vite's polling-based file watcher to fix a Docker Desktop on Windows bind-mount issue where frontend code changes were not being picked up.

## Rejected or Corrected Suggestions

- Removed a duplicate cross-field validation check (max batch size >= min batch size) from the API request schema after building a dedicated validation service function that already covered it, to avoid two places where the same business rule could drift out of sync.
- Corrected the change-type detection logic after testing against the assignment's own worked example: the initial version only ever returned RESIZE when every batch value changed, but the expected result is RESIZE and REPLACED together. Fixed by checking whether any batch value survived unchanged between the initial and final plan.
- Abandoned an initial plan to gate the API service's startup on a Docker Compose health-check dependency for the optional database service, since Compose profiles do not support that dependency cleanly when the database service is optional. Replaced with a restart-on-failure policy plus a database health check instead.

## Errors or Limitations Identified

- Vite's file watcher inside Docker Desktop on Windows silently never detected any frontend file change for the whole session, since native filesystem events do not reliably propagate through Windows bind mounts.
- The historical batch-acceptance rate only tracks batch sizes that appeared in a recommended suggestion; a batch size introduced purely through a user's edit never accumulates an acceptance rate of its own. This is a known, documented limitation rather than a bug.
- AI-suggested fixes were occasionally based on plausible-sounding but incorrect assumptions about the environment (e.g. the Docker Compose health-check dependency approach), so every suggestion still had to be verified against the actual running containers rather than trusted on its own.


## Important Decisions Made Independently

- Designed the overall system architecture: a three-layer separation between the React frontend, the FastAPI REST API, and a SQLAlchemy-backed store (SQLite for local development, Postgres for deployment), with business logic kept in framework-free service modules independent of both the web framework and the ORM.
- Designed the batch-plan generation algorithm: a backtracking search over a candidate set built from preferred sizes plus the minimum, maximum, and a fixed step, with early pruning of unreachable branches, canonical deduplication, and a hard cap on explored nodes.
- Designed the ranking formula and its weighting: preferred-size matches, equal-batch-size bonus, a penalty for near-minimum remainder batches, and a penalty for unnecessary batch count, combined into a single explainable score.
- Designed the similarity formula as a weighted blend of quantity difference and batch-count difference between the initial and final plan, rather than a single raw metric.
- Designed the change-type classification logic, using multiset comparison (subset, superset, equal length) to distinguish accept, resize, split, merge, add, remove, and replace.
- Decided that historical learning would be rule-based counting (batch-acceptance rate, similar-order pattern matching, recency weighting) rather than a trained model, and that it would only ever apply a capped, additive bonus that can never override validation.
- Decided to defer any machine-learning component entirely to future work, to be introduced only once enough historical decision data has been collected to train and validate one meaningfully.

## How AI-Generations were Verified

- A 42-test automated pytest suite covers generation, similarity, change detection, decisions, analytics, and historical learning, run after every change to confirm nothing regressed.
- Every new API endpoint was exercised live against the running Docker containers with real requests, not just unit tests, before being considered complete.
- The frontend was type-checked under the project's strict TypeScript configuration after every change, and each new module was requested directly through the dev server to confirm it compiled and transformed without error.
- Container logs were read directly to diagnose root causes (the Vite watcher issue, the Postgres startup race, the Render build failure) rather than guessing at fixes.
- The historical-learning bonus was verified end to end by comparing a plan's score before and after seeding repeated decisions, confirming it shifted measurably without ever overtaking the top-ranked plan or bypassing validation.




