# Relay — contributor and agent instructions

## Product contract

Local digital-resource sharing MVP: text, code, PDF/TXT/MD/CSV documents, and HTTP/HTTPS links. Mandatory expiry, unlisted share URLs, browser-owned workspace, manual revocation. No payments, logistics, accounts, public feed, or collaboration without explicit scope approval.

Read `docs/REQUIREMENTS.md`, `docs/DECISIONS.md`, and `docs/SECURITY.md` before changing behavior.

## Stack and commands

- Python 3.11+, Flask, Jinja, standard-library SQLite/unittest.
- Install: `python -m pip install --only-binary=:all: -r requirements.txt`
- Start: `python app.py`
- Tests: `python -m unittest discover -s tests -v`
- Cleanup: `python -m flask --app app:create_app cleanup`
- Advisory check: install development-only `pip-audit`, then `python -m pip_audit -r requirements.txt`.
- Use `.venv/bin/python` on Linux/macOS if the environment is not activated.

## Files and conventions

- `app.py`: app factory, validation, persistence, routes, CLI.
- `templates/`: escaped Jinja views.
- `static/`: dependency-free CSS/JS.
- `tests/`: isolated, real SQLite/filesystem integration tests.
- `instance/`: generated private data; never commit or expose.
- `SETUP.md`: **startup/setup instructions only**. Architecture, tests, demos, and rationale belong elsewhere.
- Keep docs consistent with actual behavior; explicitly distinguish roadmap from implementation.
- Follow Conventional Commits when commits are requested. Do not post to GitHub without approval of exact text.

## Invariants

1. Both resource preview and download must enforce server-time expiry/revocation.
2. Owner authorization and CSRF protection are mandatory for mutations.
3. Share URLs are bearer capabilities. Do not put them in analytics, third-party requests, or public logs.
4. Do not call unlisted links private, encrypted, or copy-proof.
5. Never render submitted code/HTML/Markdown as trusted HTML or execute it.
6. Never fetch submitted links on the server without a separate reviewed SSRF design.
7. Uploads stay outside static root, under random server-selected keys.
8. Validate on the server even when the browser validates.
9. Use parameterized SQL and preserve Jinja autoescaping.
10. Deny access before attempting payload deletion on revoke.
11. Physical expired-data removal is separate from access denial; do not claim scheduled cleanup exists.
12. Do not weaken tests or add dependencies/services merely to get a check passing.

## Change workflow

- Write a failing regression test before behavioral changes.
- Implement a thin slice; run the focused test, then the full suite.
- For UI changes, verify in a browser at desktop/mobile sizes and check console errors.
- Preserve core no-JS form flows and visible focus styles.
- Runtime dependencies are pinned; resolve and audit changes deliberately. Install binary distributions; do not blanket-enable third-party build scripts.
- Never overwrite/reset user work, delete data directories, or rotate the signing key without explicit approval.
- No production deployment is implied by a request for a local feature.

## Browser support

Current evergreen Chromium, Firefox, and Safari are the intended targets, not an exhaustive tested support matrix. Use native controls and feature detection. Clipboard failure must leave a manual-copy path. Prefer reduced-motion-safe, progressively enhanced behavior.

## Done means

Tests pass; relevant runtime behavior is verified; no new security bypass; requirements/decision/security/demo docs reflect changes; `SETUP.md` remains instruction-only. Report any unverified environment or known limitation honestly.
