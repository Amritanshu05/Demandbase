# Security and limitations

## Trust boundaries and assets

- Browser → application: fields, cookies, form tokens, filenames, file bytes, share tokens.
- Application → SQLite/filesystem: persisted content and ownership metadata.
- Share page → external destination: explicitly initiated by recipient, not fetched by server.
- Operator → local storage: the operator controls and can read everything on disk.

Assets: resource content, owner authorization, access-link confidentiality, disk availability.

## Abuse cases and protections

| Abuse | Implemented protection | Remaining limitation |
| --- | --- | --- |
| Guess another share | Cryptographically random 24-byte URL-safe share token | A copied/leaked valid URL grants access |
| Revoke another owner's share | Owner-secret hash check on every revoke | Browser cookie/signing-key compromise breaks authorization |
| Cross-site form submission | Random session CSRF token, constant-time comparison, SameSite cookie | No production penetration test |
| Inject scripts through paste/title | Jinja autoescaping; text-content copy; strict CSP; no HTML rendering | External files/links can still be malicious |
| SQL injection | Parameterized SQL | Application/server compromise still exposes database |
| File path traversal | Sanitized download filename, random storage key, private upload directory, guarded deletion | Local disk and database are trusted, not attacker-writable |
| Upload arbitrary active content | Allowlisted extensions, PDF signature/UTF-8 checks, forced attachment, nosniff | No malware scanning; PDF header is not full structural validation |
| Read after expiry/revoke | Check lifecycle on both preview and download; no-store; no static-file URL | Already authorized/in-flight reads and copied content cannot be revoked |
| Server-side URL-fetch attacks | No URL fetching at all | User may explicitly navigate to an unsafe external site |
| Storage flooding | 5 MiB documents, request caps, content cap, persistent browser quotas | Reset cookies/multiple browsers bypass quotas; no global/IP/disk budget |
| Host-header poisoning | Flask trusted loopback host allowlist | Hosted origins require explicit allowlist configuration |
| Referrer/cache leaks | No-referrer, no-store/private, no indexing, no third-party assets | Link tokens still appear in browser history and development-server access logs |

Session cookies are signed, not encrypted; no resource payload is stored in them. They are HttpOnly and SameSite=Lax. Secure cookies are off solely for loopback HTTP; turn them on only with HTTPS.

## Ownership and recovery

No account, password, email, or recovery secret is collected. Ownership persists for the browser's active session cookie, with a 30-day lifetime refreshed by activity. Clearing cookies or changing hostname loses management access. The share remains available until expiry unless an operator intervenes.

The signing key is generated on first run and must persist across restarts. Do not commit it, expose the data directory, or reuse the test key.

## Retention

- Revocation immediately denies requests and clears inline payloads; document removal follows.
- Expiry immediately denies new requests but does not physically delete data.
- Cleanup removes expired/revoked database rows and referenced files.
- No scheduler, backups, forensic erasure, or complete compliance workflow exists.
- Browser cookies expire independently of resource lifecycle.
- Quotas use current database rows; cleanup can remove revoked quota history. They are a local guard, not durable abuse accounting.

The local server's default request logs can contain share paths. Do not publish demo logs. A public installation needs redaction at the proxy/server and a documented access-log retention policy.

## Before any public release

- Replace the development server with a supported WSGI server behind TLS.
- Configure trusted hosts, Secure cookies, and deliberate proxy trust.
- Decide on recoverable user identity before promising ownership recovery.
- Add global/IP/account rate limits, atomic quotas, total disk budget, and request timeouts.
- Add malware scanning/quarantine for uploaded files.
- Schedule/retry cleanup and detect orphaned documents.
- Redact bearer paths from logs; define retention and backups.
- Test concurrent expiry/revocation/download behavior and relevant browser configurations.
- Audit dependencies, restore from backups, and run an independent security review.

Payments, secrets management for user uploads, and privacy-regulation compliance are not features of this MVP. Do not upload credentials, API keys, or sensitive personal documents.
