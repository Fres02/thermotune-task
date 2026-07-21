# AI Usage

## Tools Used

- Claude (Anthropic, Sonnet 5) and ChatGPT - used for frontend development (React/Vite UI), test case generation (the automated pytest suite), and sample data verification (confirming sample payloads produce the documented results against the live API).

## Where/How It Was Used

- Frontend development: building the React components (OrderForm, SuggestionsList, BatchEditor, FeedbackForm, Dashboard), the API client layer, and styling.
- Test case generation: writing the pytest suite (test_generate.py, test_similarity.py, test_change_detect.py, test_decision.py, test_analytics.py, test_history.py), including the fixtures for an isolated in-memory test database.
- Sample data verification: creating the example payloads in sample-data/ and confirming each one produces the documented result (correct scores, error messages, change types) against the live running API before writing them down.
- Debugging confirmation: used to diagnose and confirm the root cause of real issues hit during development, including a Vite file-watcher failure under Docker Desktop on Windows (bind-mount fs events not propagating), a Postgres startup race condition in Docker Compose, an internal-UUID leak in one API response field, and the Render deployment failure caused by the free-tier database limit.
