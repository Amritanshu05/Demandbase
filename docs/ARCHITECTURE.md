# Architecture

## System shape

```text
Owner browser / recipient browser
          │ HTTP on loopback
          ▼
Flask application
  ├─ signed session + CSRF validation
  ├─ resource/owner/lifecycle validation
  ├─ Jinja pages + local CSS/JS
  ├─ SQLite metadata and text/code/link content
  └─ private filesystem document payloads

Operator ── Flask cleanup command ── expired rows/files
```

Python 3.11+, Flask 3.1.x, standard-library SQLite/unittest, Jinja templates, vanilla CSS and progressive-enhancement JavaScript. No frontend bundler or network-loaded fonts/scripts.

This is a modular-enough single application, not microservices: one deployable process and direct functions whose responsibilities are visible in `app.py`. The database factory, lifecycle predicate, and payload removal are shared helpers to keep enforcement consistent.

## Storage

The default `instance/` directory is generated at startup and ignored by Git:

- `relay.sqlite3`, plus SQLite WAL/SHM sidecars while active.
- `secret.key`: random persistent signing key, created with restrictive permissions.
- `uploads/`: files named only by random storage keys.

Set `RELAY_DATA_DIR` to use a different directory. It must be local, trusted, writable, and persistent; do not use a network filesystem for the database.

## Data model

One share owns one resource; no separate users table exists.

| Column | Meaning |
| --- | --- |
| `id` | Random URL-safe bearer token; primary key |
| `owner_hash` | SHA-256 digest of browser owner secret |
| `title`, `kind`, `language` | Display metadata; kind constrained in SQL |
| `content` | Text/code/URL; empty for documents |
| `filename` | Sanitized original download name |
| `storage_key` | Random document filename, never user supplied |
| `size` | UTF-8 content bytes or uploaded-file bytes |
| `created_at`, `expires_at` | UTC Unix seconds |
| `revoked` | Irreversible lifecycle flag |
| `views` | Non-owner GET page requests, not unique visitors |

Indexes cover `(owner_hash, created_at DESC)` and `expires_at`. SQLite WAL improves reader/writer coexistence, not simultaneous writer capacity.

Status is computed, never stored:

```text
revoked flag → revoked
else expires_at <= server_now → expired
else → active
```

Revocation takes precedence over expiry for dashboard display.

## Route contract

| Method | Route | Behavior |
| --- | --- | --- |
| GET | `/` | Browser-owned dashboard; optional `q`, `kind`, `state` |
| GET | `/new` | Creation form |
| POST | `/shares` | Validate, persist, redirect 303 to share page |
| GET | `/s/<token>` | Check access, render resource; count recipient GET |
| GET | `/s/<token>/download` | Check access again; attachment response |
| POST | `/s/<token>/revoke` | Require owner + CSRF; deny access and remove payload |
| GET | `/health` | Database liveness check |

Responses are HTML, redirects, or downloads except for the JSON health endpoint. This MVP intentionally does not claim a public REST API contract.

Status codes: 200 successful read, 303 successful mutation redirect, 400 invalid request/host, 403 CSRF failure, 404 unknown/not-owned resource, 410 closed resource, 413 request too large, 422 invalid fields/file, 429 local creation quota.

## Creation flow

1. Generate browser owner and CSRF tokens if absent; store in signed HttpOnly session cookie.
2. Require CSRF token on POST.
3. Validate title, enums, content or document bytes.
4. Check persistent per-owner quotas: fewer than 60 creations in the preceding hour and fewer than 100 active shares.
5. Generate share token and optional storage key.
6. Write document outside static root and insert metadata; remove the just-written document if SQL fails.
7. Commit and redirect. The resulting URL is a capability: possession allows reading while active.

There is no transaction spanning SQLite and the filesystem. Compensating cleanup handles ordinary insertion errors; a process crash between file write and database commit can leave an orphaned file. See scaling/operations work.

## Access and revocation

Every page/download request reads the share and checks current state before returning payload. Nothing serves files directly from a public directory.

Revocation first commits `revoked=1` and clears inline content, then removes the document. A file-deletion failure can leave bytes on disk but does not restore web access. Re-running cleanup retries payload deletion.

Authorization is evaluated when the request starts. A concurrent revocation cannot claw back bytes already read or terminate an in-flight authorized download. No claim of globally atomic revocation is made.

## Expiry and physical retention

Expiry is lazy/request-time access enforcement; no background worker is required for correct denial. Files and rows remain until:

```bash
python -m flask --app app:create_app cleanup
```

This command deletes expired/revoked documents and their rows, including metadata. Closed links become 404 after cleanup. For a long-running deployment, schedule cleanup externally and monitor failures. No scheduler is installed by the MVP.

SQLite logical deletion is not forensic erasure of database pages/WAL, disks, snapshots, or backups. The app does not create backups.

## Configuration

- `PORT`: local server port, default 5000.
- `RELAY_DATA_DIR`: persistent local data directory, default `instance`.
- `RELAY_SECURE_COOKIE=1`: require HTTPS cookies when deployed behind TLS. Do not enable for ordinary local HTTP.
- Flask factory overrides are used for isolated tests and an injected clock.
- Trusted hosts default to localhost, 127.0.0.1, and IPv6 loopback. Public hosting needs an explicit configured allowlist and deployment work.
