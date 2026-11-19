# Research and resulting choices

## Method

Desk research of public product documentation and official engineering references, reviewed on 19 November 2026. This is not a market-sizing exercise, competitive benchmark, or user study. Features below are statements from the linked documentation, not independently tested competitor behavior.

## Product references

### Pastebin

Source: https://pastebin.com/faq

The FAQ describes text/source-code sharing, public/unlisted/private visibility, configurable expiry, per-user management, input size caps, and spam limits. It distinguishes an unlisted paste from a private, authenticated paste.

**Applied:** a low-friction paste workflow, explicit expiry, readable code, owner management, bounded inputs, and the term **unlisted**.

**Changed deliberately:** Relay has no public feed and requires every resource to expire. It handles documents and links as first-class resource types rather than calling everything a paste.

### PrivateBin

Source: https://privatebin.info/

PrivateBin documents browser-side encryption, optional passwords, expiry, burn-after-reading, syntax highlighting, and optional uploads. It also explains that a shared URL can grant access and that trust in delivered client code remains important.

**Applied:** make access semantics and limitations visible, avoid promising that a temporary URL is confidential.

**Deferred:** end-to-end encryption and burn-after-reading. Correct key management and single-read concurrency are separate product/security projects. Relay explicitly stores readable content on the server.

## Technical references

| Reference | Finding used | Result |
| --- | --- | --- |
| [SQLite: appropriate uses](https://www.sqlite.org/whentouse.html) | Local/low-concurrency applications benefit from simplicity; many concurrent writers or multiple hosts favor a client/server database | SQLite locally; PostgreSQL migration when write contention/multi-host deployment requires it |
| [Flask upload pattern](https://flask.palletsprojects.com/en/stable/patterns/fileuploads/) | Untrusted filenames and unbounded uploads are unsafe | Random storage keys, sanitized download names, size caps |
| [Flask web security](https://flask.palletsprojects.com/en/stable/web-security/) | Escaping, CSRF, cookie flags, trusted hosts, and security headers require explicit care | Jinja escaping, CSRF tokens, signed HttpOnly sessions, host restrictions, CSP |
| [Flask file responses](https://flask.palletsprojects.com/en/stable/api/#flask.send_file) | File-response defaults can include conditional/range/cache behavior | Authorization first; disable conditional responses and ETags; no-store on every response |
| [OWASP upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) | Defense in depth: allowlists, size limits, storage separation, scanning | Implement basic checks; document that magic bytes do not prove safety and malware scanning is absent |
| [Modern Web Guidance](https://github.com/GoogleChrome/modern-web-guidance) — forms | Semantic forms, visible labels, native constraints, server validation, delayed feedback, status announcements | Progressive enhancement rather than a JavaScript-only application |

Flask API usage was additionally checked through its official repository documentation via Context7 before implementation. OWASP is a further-reading reference, not a claim of a completed formal security audit.

## Central design insight

**Temporary availability is not digital rights management.** Closing Relay access does not remove a downloaded PDF, copied snippet, browser screenshot, or the original external website. The interface explains this at creation and consumption.

## Open validation questions

1. Do target users value browser-only setup more than account-based ownership recovery?
2. Are PDF/TXT/MD/CSV sufficient, or is DOCX essential?
3. Is a one-day default expiry appropriate for typical sharing?
4. Can a first-time recipient identify the expiry and external-link destination without explanation?
5. Does language labeling suffice, or is syntax highlighting a core expectation?

Next research step: observe five representative users completing creation, recipient access, and revocation. Record completion failures and confusion before expanding functionality.
