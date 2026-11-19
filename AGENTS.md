# Campus Commons — agent and contributor guide

## Product

Build the physical-item borrowing MVP described in `Community_Resource_Sharing_MVP_v0.1.md`, with the agreed additions in `README.md`. Members list movable goods, request borrowing, approve/reject, and record returns. Approved borrowers see fictional owner contact details. Keep delivery local; no chat, payments, uploads, real authentication, or reservations.

## Implementation

- Python 3.9+, Flask, Jinja, standard-library SQLite; no frontend build.
- `app.py` owns routes, validation, seed data, and transactions. Templates and static assets provide the UI.
- `instance/` is generated runtime data. Never commit, overwrite, or delete a user's database or signing key.
- Seed Amritanshu, Rahul, and Priya once. Demo identity selection is intentionally not secure authentication.
- Enforce owner checks and valid state transitions in the backend. Never trust submitted owner/member fields.
- Approval must recheck availability inside a write transaction, reject competing Pending requests, and preserve the unique Approved-per-item database index.
- Keep SQL parameterized, templates escaped, and POST forms CSRF-protected.
- Keep core forms usable without JavaScript and retain visible keyboard focus.

## Commands and completion

- Setup/run: follow `STARTUP.md`; start with `.venv/bin/python app.py`.
- Windows PowerShell/Command Prompt: start with `.\.venv\Scripts\python.exe app.py`.
- Focused verification: `.venv/bin/python -m unittest discover -s tests -v`.
- Windows verification: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
- Prioritize the working MVP over extensive test coverage. Add checks for material lifecycle/data-integrity changes, not cosmetic edits.
- Update the README, design, tradeoffs, and demo guide when behavior changes. `STARTUP.md` contains run instructions only.
- Preserve unrelated user changes. Do not restore the intentionally removed digital-sharing app.
- Report actual checks and any verification limits. Do not publish, commit, or push unless requested.
