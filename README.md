# Campus Commons

**Good things. Better shared.**

A working, local community resource sharing MVP: list a physical item, request to borrow it, let the owner approve or reject, and record its return. Listings and requests live in SQLite and survive refreshes and restarts.

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

Stop the server with **Ctrl+C** first. Run the commands below from the project directory. This removes all custom listings and request history; restarting recreates the three demo members and six original items. The session signing key is kept.

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

Optionally copy `commons.sqlite3` elsewhere before removing it if you want to keep the current data. If you set `COMMONS_DATA_DIR`, use the `commons.sqlite3` file in that directory instead of `instance/`. Keep `secret.key`; you do not need to remove the entire `instance/` directory.

## What works

- Browse available items and create listings with a category, description, and condition.
- Switch between Amritanshu, Rahul, and Priya. Every member can lend and borrow.
- Submit a request with an expected return date of today or later.
- View incoming and outgoing requests in My Activity.
- Owners approve or reject requests and record returns.
- Approval locks the item and automatically rejects competing pending requests.
- Approved borrowers see an “Accepted” card with the owner's fictional email and expected return date. Arrange handovers outside the app; there is no chat.
- Returned items reappear in Explore; request history stays in My Activity.
- Backend validation, owner-only actions, CSRF-protected forms, and database integrity checks.

## Demo members

| Member | Demo contact | Initially sharing |
|---|---|---|
| Amritanshu (default) | amritanshu@example.com | Cordless Drill, Badminton Set |
| Rahul | rahul@example.com | Cricket Bat, Camping Tent |
| Priya | priya@example.com | Mini Projector, The Design of Everyday Things |

The member selector works without logging in. With JavaScript it switches immediately; otherwise select a member and press **Switch**. Identity changes are scoped to the browser session, including its tabs. Separate browser profiles can select different members independently.

## Quick demo

As Amritanshu, request Rahul's Cricket Bat with a future return date. Switch to Rahul and approve it in My Activity. Switch back to Amritanshu to show the approval and `rahul@example.com` contact card. Switch to Rahul and mark it returned; the bat becomes available again. Refresh to show persistence.

For competing approvals and listing creation, follow the [full demo walkthrough](docs/DEMO.md).

## Documentation

| Document | Purpose |
|---|---|
| [Original MVP brief](Community_Resource_Sharing_MVP_v0.1.md) | Product requirements and exclusions |
| [Startup](STARTUP.md) | Installation and run instructions only |
| [Design](docs/DESIGN.md) | Architecture, screens, data model, routes, and state changes |
| [Tradeoffs](docs/TRADEOFFS.md) | Choices, limitations, and deferred capabilities |
| [Demo](docs/DEMO.md) | End-to-end judging walkthrough |
| [Agent instructions](AGENTS.md) | Contributor conventions and project commands |

Agreed changes to the original brief: use **three** seeded members; show demo owner contact after approval; deliver **locally**, replacing the deployed-URL acceptance requirement. The original brief is retained unchanged.

## Verification

Three focused integration checks exercise the lifecycle and contact card, competing approvals and the database guard, and backend validation/access control. They use temporary databases and do not modify your demo data.

macOS / Linux:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Windows PowerShell or Command Prompt:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Project layout

```text
app.py                  Flask app, SQLite storage, routes, and seed data
templates/              Server-rendered pages and shared components
static/                 Local CSS, JavaScript, and favicon
tests/test_lifecycle.py  Focused integration checks
docs/                   Design, tradeoffs, and demo walkthrough
instance/               Generated database and signing key (gitignored)
```

## Limits

This is a hackathon demo. The selectable identities are **not authentication**; anyone using the app can choose any member. Contacts are fictional. The application records decisions, not physical handovers. It runs on your machine's loopback interface using Flask's development server and is not deployed or production-ready.

There are no payments, uploads, chat, notifications, search, real identity checks, delivery scheduling, or future reservations. Dates use the community timezone, Asia/Kolkata. Demo data is seeded once; restarting never resets your activity. Keep `instance/` to preserve data.
