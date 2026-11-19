# Product requirements

## Problem and target user

Students, developers, and small teams repeatedly pass snippets, reference documents, and useful URLs through chat. Permanent uploads create forgotten access; heavyweight file platforms add friction. Relay provides a small, explicitly temporary sharing workflow.

**Product promise:** create a resource, choose its lifetime, and share one URL. Stop future access automatically at expiry or manually by revoking.

This is a product hypothesis, not a validated claim about market demand. No user interviews or usability study have been conducted.

## Actors

- **Owner:** browser holding the signed session that created a resource.
- **Recipient:** anyone holding the resource's unlisted URL.
- **Local operator:** starts/stops the app, maintains its files, runs cleanup.

## Capability map

| Capability | Included | Boundary |
| --- | --- | --- |
| Resource creation | Text, code, document upload, external link | One resource per share; immutable |
| Access lifecycle | Mandatory expiry, manual revocation | Cannot revoke saved copies |
| Consumption | Escaped preview, copy, download, open link | PDFs download-only; no code execution |
| Management | Browser-owned list, search, filters, counts | Latest 200 records; no cross-device accounts |
| Persistence | Local SQLite, filesystem uploads, stable signing key | Single-host installation |
| Operations | Health route, cleanup CLI, isolated tests | No production hosting or scheduling |

## User stories and acceptance criteria

### Create text or code

As an owner, I can paste content and receive a share URL.

- Title is required, trimmed, and limited to 120 characters.
- Non-empty text/code is limited to 100,000 characters.
- Code whitespace is preserved. A language label is stored; syntax coloring is not implemented.
- Server validation rejects unknown resource kinds, expiry values, and language values.
- Successful form submission redirects to the preview; refreshing does not resubmit creation.
- Invalid values remain in the form with a descriptive error.

### Upload a document

As an owner, I can upload a supported document and share it without exposing its storage path.

- Allowed formats: PDF, TXT, MD, CSV.
- File is non-empty and no larger than 5 MiB.
- PDF must start with a PDF header; text documents must decode as UTF-8 and contain no NUL bytes.
- File is stored under an opaque server-generated key, outside the static directory.
- Text preview displays at most the first 20 KB as escaped text; PDFs are downloaded as attachments.
- Validation errors require reselecting the file; browsers cannot restore file inputs.

### Share a link

As an owner, I can store an HTTP/HTTPS URL and present its destination to a recipient.

- Destination must have a host and no credentials, whitespace, control characters, or backslashes.
- URL is limited to 2,048 characters.
- The server never fetches the URL or generates a remote preview.
- Recipient must explicitly click to visit the external destination.

### Consume and close access

As a recipient, I can access a valid share without signing up.

- Preview and download independently enforce expiry/revocation.
- Expiry is evaluated against server time; equality with the expiry timestamp is expired.
- Missing share returns 404; expired/revoked share returns 410 until cleanup removes it, then 404.
- After revocation, the share cannot be restored; a new share requires a new URL.
- Requests authorized before expiry/revocation may complete. Already downloaded/copied content remains available to the recipient.

### Manage my shares

As an owner, I can find and revoke my resources.

- Other browser sessions cannot list or revoke my resources.
- Title search is case-insensitive; filters include type and lifecycle state.
- Active, expired, and revoked counts describe the most recent 200 owned records.
- Recipient page views exclude owner views and HEAD requests; refreshes count again. These are not unique visitors or download counts.
- Owner cookie lasts up to 30 days and refreshes with activity. No recovery mechanism is included.

## Nonfunctional goals

- Local startup needs Python and one dependency-install command; no cloud credentials, Node build, Docker, or external database.
- Persistent resources remain available after server restart.
- Keyboard navigation, visible labels, mobile layout, meaningful error states, and copy fallback.
- Automated tests cover the main flows and security boundaries.
- No claims of measured throughput, production readiness, encryption, or regulatory compliance.

## Explicit exclusions

Payments; logistics; physical-resource lending; arbitrary file types; image/video hosting; public browsing; accounts/passwords; edit/version history; collaboration; rich Markdown rendering; executing code; end-to-end encryption; burn-after-reading; email notifications; production deployment.

## Completion definition

All automated tests pass; desktop and mobile pages are inspected in a real browser; create → recipient preview/download → revoke is demonstrated; setup steps are reproducible; documentation distinguishes current behavior from future work.
