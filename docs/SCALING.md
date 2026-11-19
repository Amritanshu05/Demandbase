# Growth and scaling roadmap

## Current boundary

One local host, Flask development server, SQLite WAL, private local files, browser-based ownership, latest-200 dashboard, manual cleanup. This is real local persistence with a migration path—not a horizontally scalable production deployment.

No throughput or concurrency benchmark has been performed. Move based on evidence, not imaginary traffic targets.

## Stage 1 — reliable small hosted installation

Before inviting external users:

1. Supported WSGI server, TLS reverse proxy, configured hostname allowlist, Secure cookies.
2. Redact share URLs from logs; retain status/duration/request IDs without payloads or bearer tokens.
3. Recoverable account ownership if users need cross-device management; migrate browser-owned resources through an authenticated ownership-claim flow.
4. Global request limits and atomic account/IP quotas, plus a hard storage budget.
5. Scheduled cleanup with retries, orphan reconciliation, alerts, and deletion metrics.
6. Consistent database/filesystem backups and a restore drill; understand SQLite WAL backup semantics.
7. SQL-side filters and cursor pagination; current dashboard searches only the latest 200 rows.
8. Malware scan/quarantine workflow for uploaded documents.

Remain on a single host with SQLite if measured workload permits. Do not put SQLite on a shared/network filesystem to simulate a distributed database.

## Stage 2 — multiple application instances

**Triggers:** multiple hosts are required, SQLite busy/lock errors rise, or write latency violates a defined service objective.

- Migrate metadata/text to PostgreSQL; preserve UTC timestamps and lifecycle semantics.
- Add versioned schema migrations and a verified migration script, not a manual data copy.
- Move uploads to private object storage with opaque keys.
- Share session-signing configuration deliberately; consider server-side sessions for revocable login.
- Replace per-browser quotas with shared, atomic limits.
- Enforce authorization centrally before every payload delivery.
- Keep expiry/revocation state authoritative in the database.

**Signed-object-URL caveat:** a presigned download URL can remain valid after application revocation. If immediate denial for newly started requests is required, proxy downloads through the application/access gateway instead of issuing long-lived object URLs. Even a proxy cannot recall bytes already delivered.

## Stage 3 — read-heavy growth

**Triggers:** measured database/egress pressure or global latency requirements.

- Separate view analytics from synchronous resource reads; queue/aggregate them.
- Cache nonsensitive static assets, but avoid public caching of bearer-protected resource bodies.
- If metadata caching is introduced, enforce expiry locally and design revocation invalidation explicitly.
- Add bounded storage/retention tiers and account quotas.
- Introduce direct-to-private-storage uploads only with upload authorization, completion verification, size constraints, and quarantine.

## Observability to add

- Request count, status, latency distribution, and server error rate.
- Expired/revoked access denials without logging tokens.
- Database lock/busy events and query latency.
- Used storage, upload failures, rejected files, scan outcomes.
- Cleanup backlog age, run result, retry/orphan counts.
- Backup age and restore-drill outcome.

Health currently checks that SQLite can execute a query; it does not prove available disk capacity, cleanup health, or production readiness.

## Evolution principles

Keep create/read/revoke behavior stable while replacing infrastructure. Add boundaries only where there is a second implementation or a real operational need. Do not introduce microservices, queues, Redis, or Kubernetes merely to demonstrate “scalability.”
