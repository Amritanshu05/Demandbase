# Campus Commons

**Good things. Better shared.**

A working local sharing MVP: search community items, check each calendar, request dates, get approval, coordinate in chat, and let the owner record handover and return. Listings, reservations, personal inventory, and messages persist in SQLite.

## Run

Follow [STARTUP.md](STARTUP.md) for first-time installation on macOS/Linux or Windows. Once installed, start from the project directory:

**macOS / Linux**

```sh
.venv/bin/python app.py
```

**Windows — PowerShell or Command Prompt**

```powershell
.\.venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:5001**. No external services or API keys are required.

## Reset the demo database

Stop the server with **Ctrl+C** first. Run the commands below from the project directory. This removes all custom listings, reservations, owner date blocks, and chat messages; restarting recreates the three demo members and six original items. The session signing key is kept.

**macOS / Linux**

```sh
rm instance/commons.sqlite3
.venv/bin/python app.py
```

**Windows PowerShell**

```powershell
Remove-Item .\instance\commons.sqlite3
.\.venv\Scripts\python.exe app.py
```

**Windows Command Prompt**

```bat
del instance\commons.sqlite3
.\.venv\Scripts\python.exe app.py
```

Optionally copy `commons.sqlite3` elsewhere before removing it if you want to keep the current data. If you set `COMMONS_DATA_DIR`, use the `commons.sqlite3` file in that directory instead of `instance/`. Keep `secret.key`; you do not need to remove the entire `instance/` directory. Old migration backups in `instance/backups/` are retained by this reset.

## What works

- Search item names, combine category filters, and open full item details.
- A monthly calendar for every listing, with previous/next navigation, click-to-select ranges, and ordinary date fields as a no-JavaScript fallback.
- Owner blocks for dates the item is unavailable. Public calendars show only availability, not borrower names or chat.
- Multiple approved reservations for non-overlapping dates. Ranges are full-day and inclusive: 1–10 blocks the 10th; a separate reservation can start on the 11th.
- Pending requests reserve nothing. Approval rechecks availability and rejects only overlapping pending requests.
- Owner-only **Mark handed over** starts actual borrowing. Owner-only **Mark as returned** confirms receipt and releases remaining reserved dates immediately.
- Borrowers cancel Pending requests; either participant can cancel Approved reservations before handover.
- Unstarted Pending/Approved periods expire after their end date during normal app operations.
- Overdue Active items remain lent out. New reservations pause; existing future approvals remain with warnings; another handover waits for return.
- Owner edit, pause/resume, archive/restore. Approved or Active commitments lock editing/pause/archive. Pausing or archiving declines Pending requests; history is kept.
- My Dashboard contains all inventory, incoming decisions, upcoming reservations, awaiting handover, active lending/borrowing, history, and overdue alerts.
- Borrow-specific plain-text chat, manual refresh, and secondary fictional owner contact details. Closed, previously approved conversations remain read-only.
- Backend validation, CSRF-protected forms, owner/participant checks, transactional writes, database overlap guards, and one Active physical borrow per item.

## Demo members

| Member | Demo contact | Initially sharing |
|---|---|---|
| Amritanshu (default) | amritanshu@example.com | Cordless Drill, Badminton Set |
| Rahul | rahul@example.com | Cricket Bat, Camping Tent |
| Priya | priya@example.com | Mini Projector, The Design of Everyday Things |

Choose a member in the header. With JavaScript it switches immediately; otherwise press **Switch**. The selected identity is shared by tabs in that browser session. Separate browser profiles can select members independently. These identities are not authentication.

## Quick demo

As Amritanshu, search for Rahul's Cricket Bat, open its calendar, and request **today through a later return date**. Switch to Rahul and approve the dates. Switch back to Amritanshu to open chat. Rahul then chooses **Mark handed over**, and later **Mark as returned**. The actual borrow closes, its unused days become free, and its chat becomes read-only.

For future scheduling, request next month's 1–10 as Amritanshu and 20–25 as Priya. Rahul can approve both in advance. They remain reservations until Rahul records handover during the respective booked period. Use [the full demo guide](docs/DEMO.md) for owner blocks, cancellation, and listing controls.

## Upgrade existing data — no reset needed

Stop the old process and start the updated app normally. An existing pre-calendar database is copied to `instance/backups/commons-before-calendar-<UTC timestamp>.sqlite3` before migration. Keep this directory private and out of GitHub, along with the rest of `instance/`.

The migration preserves listing/request/message IDs, seed data, signing key, and history. Old **Approved** records become **Active**, matching the earlier app's approval-as-borrowing semantics. Legacy start dates come from request creation dates in Asia/Kolkata. Unknown actual handover/return timestamps remain empty. New records store actual lifecycle timestamps.

The migration verifies foreign keys and rolls back on failure. A successful restart does not repeat the backup or reseed data. If startup reports a migration problem, keep the database and backup and resolve the reported error; do not delete `instance/` to work around it. No separate SQLite installation or migration command is required.

## Documentation and scope

| Document | Purpose |
|---|---|
| [V0.1 brief](Community_Resource_Sharing_MVP_v0.1.md) | Original historical scope |
| [V0.3 brief](Community_Resource_Sharing_MVP_v0.3.md) | Dashboard/chat proposal |
| [V1.0 review](Community_Resource_Sharing_MVP_Review_and_Redesign_v1.0.md) | Product review, retained as supplied; its Express ZIP audit is not an audit of this Flask app |
| [Startup](STARTUP.md) | Setup/run commands for Windows and macOS/Linux |
| [Design](docs/DESIGN.md) | Implemented behavior, schema, interfaces, migration, and invariants |
| [Tradeoffs](docs/TRADEOFFS.md) | Chosen policies and deferred features |
| [Demo](docs/DEMO.md) | Reproducible walkthrough |
| [Agent instructions](AGENTS.md) | Contributor conventions |

The agreed scope combines the review's discovery/listing-control improvements with date calendars, future reservations, owner-only handover/return, cancellation, and overdue handling. Keep **Flask/Jinja + SQLite**, server-rendered navigation, and **local-only delivery**. These choices override conflicting historical exclusions and suggested React/Supabase/public-hosting designs.

## Verification

Thirteen focused integration checks use temporary databases, leaving visible demo data untouched. They cover lifecycle and access control, disjoint/overlapping ranges, two simultaneous approvals, owner blocks/listing controls, cancellation/expiry, late and early returns, chat, and legacy migration including failure rollback.

macOS / Linux:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Windows PowerShell or Command Prompt:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The Chrome walkthrough checks discovery, calendar clicks across months, two approved reservations, owner handover, chat, early return, cancellation, pause/resume/archive/restore, and phone/tablet/desktop widths. Native Windows runtime verification has not been performed in this macOS workspace.

## Project layout

```text
app.py       Flask routes, forms, permissions, and lifecycle actions
booking.py   Date validation, availability, calendar, and domain helpers
storage.py   Schema, overlap guards, backed-up migration, and seed data
templates/   Server-rendered pages and shared components
static/      Local CSS, calendar enhancement, and favicon
tests/       Focused integration checks with temporary databases
docs/        Design, tradeoffs, and demo walkthrough
instance/    Generated database, signing key, and backups (gitignored)
```

## Limits

Selectable identities are **not authentication**: anyone can choose another demo member. Chat access is enforced against the selected identity, not a verified real-world identity. Use only fictional contacts and non-sensitive messages without personal phone numbers or home addresses. The app records owner assertions about handover/return; it cannot verify physical custody.

Share ordinary movable goods. Weapons, hazardous/illegal items, vehicles, account credentials, property, services, and hygiene-sensitive personal-use items are outside scope. The UI provides guidance, not automated moderation or guarantees.

No payments, uploads, general messaging, attachments, push/email notifications, hourly/recurring bookings, reservation amendments/extensions, waitlists, multiple quantities, real authentication, or public deployment. Dates use Asia/Kolkata; timestamps are UTC. The Flask development server runs locally. Keep `instance/` to preserve data.
