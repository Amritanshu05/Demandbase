# Relay

**Useful things, passed along.** A locally runnable digital-resource sharing MVP inspired by Pastebin.

Share text, code, documents, and links through unlisted URLs with mandatory expiry. Recipients need no account. Owners manage and revoke shares from their browser workspace.

## Run

See **[SETUP.md](SETUP.md)** for installation and startup instructions only.

## What works

- Text and code sharing with escaped, monospace previews and copy/download actions.
- PDF, UTF-8 TXT, Markdown, and CSV uploads up to 5 MiB.
- Text-document previews; PDFs are download-only.
- HTTP/HTTPS link sharing with an explicit external-destination page.
- Expiry choices: 1 minute for demos, 1 hour, 1 day, 7 days, or 30 days.
- Server-enforced expiry and irreversible revocation on both preview and download routes.
- Private browser workspace with title search, type/status filters, status counts, and recipient page-view counts.
- SQLite persistence across restarts, plus a persisted session-signing key.
- CSRF protection, owner checks, output escaping, request/upload limits, security headers, and local creation quotas.
- Expired/revoked-content cleanup command.
- Responsive, keyboard-accessible, server-rendered UI. Core create/read/revoke flows work without JavaScript.

## Documentation

| Document | Purpose |
| --- | --- |
| [SETUP.md](SETUP.md) | Instructions to install, configure, and start locally—nothing else |
| [Product requirements](docs/REQUIREMENTS.md) | Scope, user stories, acceptance criteria |
| [Research](docs/RESEARCH.md) | Sources reviewed and how they influenced the product |
| [Architecture](docs/ARCHITECTURE.md) | Request flows, data model, routes, retention |
| [Design decisions](docs/DECISIONS.md) | UI/backend choices, alternatives, tradeoffs |
| [Demo](docs/DEMO.md) | Presentation and reproducible judging walkthrough |
| [Testing](docs/TESTING.md) | Test commands, coverage, manual checks |
| [Security](docs/SECURITY.md) | Threat model, implemented protections, limitations |
| [Scaling](docs/SCALING.md) | Incremental growth path, not speculative infrastructure |
| [AGENTS.md](AGENTS.md) | Contributor/AI-agent rules and project commands |

## Important boundaries

This is a **local MVP, not a production release**. There are no accounts, payments, logistics, public discovery, editing, or collaborative workspaces.

The owner identity lives in a signed, HttpOnly browser cookie. Clearing cookies, switching browsers/hostnames, or losing the server signing key loses management access. Anyone holding a share URL can read it while active. The server operator can read stored content; there is no end-to-end encryption.

Expiry blocks new platform requests; it cannot erase saved copies or interrupt a download already authorized. Physical deletion of expired content requires running cleanup. Do not use this MVP for secrets or sensitive personal documents.

The development server binds to loopback only. URLs containing `127.0.0.1` are useful only on that machine. For the local demo, use an incognito window on the same computer.

## Project map

```text
app.py                Flask factory, validation, storage, routes, cleanup
requirements.txt      Pinned runtime dependencies
templates/            Jinja server-rendered pages
static/               Local CSS, progressive-enhancement JS, favicon
tests/test_app.py     Isolated integration/security regression tests
docs/                 Product and engineering documentation
instance/             Generated database, signing key, uploads (gitignored)
```
