# Campus Commons — contributor and agent guide

## Product

Use the implemented calendar/focused-review scope in `README.md` and `docs/DESIGN.md`. Retain source briefs as historical inputs. This is a local Flask/Jinja + SQLite demo with Amritanshu, Rahul, and Priya. No production authentication, hosting, payments, uploads, hourly/recurring bookings, or external calendar service.

## Implementation

- `app.py`: routes, forms, and actor checks. `booking.py`: availability/lifecycle/date helpers. `storage.py`: schema, migrations, and seeds.
- Keep SQL parameterized, Jinja escaped, POSTs CSRF-protected, and core forms usable without JavaScript.
- Runtime data and backups live under ignored `instance/`. Never reset user data or signing keys. Migrations must preserve records and IDs and back up existing data before schema rebuilds.
- Approval reserves an inclusive date range; multiple disjoint Approved reservations are valid. Recheck owner blocks, overlaps, listing state, and overdue custody inside a write transaction. Reject only overlapping Pending requests.
- Preserve overlap triggers and the unique Active-per-item index. Only the owner marks Handed over (Approved → Active) and Returned (Active → Returned).
- An overdue Active borrow never expires or releases automatically. Keep future approvals, pause new reservations, and prohibit another handover until return.
- Expire unstarted Pending/Approved records after their end date during app operations. Borrowers cancel Pending; either participant cancels Approved before handover.
- Owner edit/pause/archive requires no Approved/Active commitments. Pause/archive rejects Pending requests; restore never reopens old records. Owner blocks cannot override committed dates.
- Chat is tied to one request. Check participation for every read/send. Approved/Active allow writes. Returned and previously approved Cancelled/Expired chats are read-only. Unapproved records have no chat.
- Validate messages as 1–1,000 trimmed plain-text characters. Derive sender from the session. No polling or WebSockets.
- Upgrade legacy Approved to Active; derive old start dates from request creation without fabricating actual handover timestamps. Preserve IDs, messages, foreign keys, seed marker, and signing key.
- Do not re-enable unavailable calendar buttons during submit recovery. Restore only buttons tagged as disabled by the submitting form.

## Commands and completion

- macOS/Linux run: `.venv/bin/python app.py`.
- Windows run: `.\.venv\Scripts\python.exe app.py`.
- macOS/Linux checks: `.venv/bin/python -m unittest discover -s tests -v`.
- Windows checks: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
- Keep verification focused on meaningful lifecycle, migration, permission, and concurrency risks; do not add tests for cosmetic changes.
- Update README, design, tradeoffs, and demo docs when behavior changes. STARTUP.md contains setup/run instructions only, with parallel Windows/macOS commands.
- Preserve unrelated user changes; do not restore the removed digital-sharing app. Do not commit, push, publish, or reset demo data unless requested.
