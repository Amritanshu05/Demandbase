# Design decisions and tradeoffs

Status: accepted for the local MVP. These are deliberately scoped decisions, not universal recommendations.

| Decision | Why this solves the MVP | Tradeoff / revisit trigger |
| --- | --- | --- |
| Flask server-rendered application | One runtime; simple startup and direct tests; core flows work without JS | Rich interactive editing would benefit from a larger frontend architecture |
| SQLite + local documents | Real persistence without service credentials, Docker, or internet after install | One-host storage and serialized writes; move to PostgreSQL/object storage for multiple instances |
| Signed browser ownership, no signup | Immediate demo; recipients/owners do not need an external identity provider | No recovery or cross-device management; losing cookies loses ownership |
| Unlisted, mandatory-expiry shares | Low-friction access with a clear endpoint; no accidental public feed | Anyone holding the URL can read; expiry cannot recall copies |
| Immutable resource payloads | A link's content cannot silently change after sharing | Corrections require a new share, no edit/version history |
| Opaque random storage keys | User filenames never choose server paths | Need database metadata to recover original names |
| Explicit document allowlist | Useful document coverage without pretending to support every resource | No DOCX/PPTX/images; PDFs remain untrusted despite header checks |
| PDF download-only | Avoid active inline content and complexity of preview isolation | Recipient needs a PDF reader; no embedded preview |
| HTTP/HTTPS links, no server fetch | Clear external destination; avoids server-side URL-fetch SSRF surface | No rich link cards or availability checks; harmful destinations still possible |
| Plain escaped code, language label | Safe display, whitespace retention, no extra parser dependencies | No syntax coloring; add audited highlighting only if users need it |
| Server-time access predicate | Same expiry semantics on previews and downloads; no scheduler dependency | Cleanup is separate; already authorized transfers may finish |
| Deny first, delete second | A cleanup/file error cannot keep a revoked share live | Disk bytes may persist until cleanup succeeds |
| Bound latest-200 dashboard | Predictable small local queries and simple filters | Not a full-history search; add SQL filtering and pagination before larger use |
| Owner-scoped persistent quota | Restart does not reset normal limits | Cookie reset bypasses it; races can overshoot; not sufficient public abuse prevention |

## UI direction

**Relay** uses a warm paper background, near-black text, muted green lifecycle cues, and restrained orange accents. An editorial heading gives the product a recognizable identity; the workspace remains utilitarian.

- One creation page; four native radio choices reveal only relevant fields when JavaScript is available.
- Native inputs and semantic forms, not custom select/dialog frameworks.
- One-day default balances usefulness with the temporary-sharing premise.
- Status badges include words; color is never the sole status signal.
- Expiry is printed in UTC to avoid ambiguous timezone interpretation.
- A private collection is distinct from the share page: an unlisted share is not called “private.”
- Confirmation precedes JavaScript-enhanced revocation; owner text explains its irreversibility. Without JavaScript, submitting the clearly labeled revoke button is immediately effective.
- Copy controls use the Clipboard API; if unavailable, a status message directs the user to select/copy manually.
- Narrow screens collapse grids instead of shrinking controls into unusable targets.

## Alternatives not selected

### Full SPA + separate API

Useful for richer interaction, but doubles local tooling and adds asynchronous/error-state complexity for a mostly form-driven product. A frontend/API split remains possible without changing the lifecycle model.

### Cloud-backed database, storage, and auth now

Useful for hosted distribution, but unnecessary for the explicitly requested offline-capable local MVP and would require account provisioning. Current SQLite/filesystem persistence is real local storage, not a simulated cloud integration.

### Password-protected shares or end-to-end encryption

Potentially valuable, but changes the security promise and adds key/password recovery, rate-limiting, and document-handling design. It should not be bolted on under a vague “secure sharing” label.

### Burn-after-reading

Not equivalent to expiry. Bots, previews, HEAD requests, simultaneous readers, and downloads make single-read guarantees subtle. Fixed expiry plus owner revocation is easier to explain and test honestly.

## What “scalable” means here

A clear migration path, not a claim that a Flask development server and local disk can horizontally scale. Preserve lifecycle checks, replace persistence deliberately, and add deployment/abuse controls based on observed needs. See [SCALING.md](SCALING.md).
