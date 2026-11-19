# Campus Commons — decisions and tradeoffs

| Choice | Why it fits | Limitation |
|---|---|---|
| Flask/Jinja modular monolith | Reuses the working app; no frontend build or external services. Routes, booking rules, and storage have separate modules. | Page navigations rather than a React SPA. |
| SQLite | Automatic setup, transactions, overlap guards, and durable local data. | One local database; writers serialize. Multi-instance public hosting requires another operational design. |
| Inclusive whole-day ranges | Easy calendar and owner expectations. 1–10 blocks the 10th; another booking starts on the 11th. | No hourly turnover, recurring reservations, or editable/extended bookings. |
| Approval reserves; owner starts custody | Future approval no longer falsely implies the borrower has the item. | A click is an owner assertion, not proof of physical handover. |
| Multiple disjoint Approved reservations | Supports the 1–10 and 20–25 use case. | Every approval must recheck overlapping ranges. A single Approved-per-item index is insufficient. |
| Overlap triggers + unique Active index | Prevent double-booked dates and double physical custody, including stale/concurrent actions. | Small amount of domain-specific SQL; must be preserved during migration. |
| Overdue pauses new reservations | Does not advertise uncertain availability. Future approvals are kept with warnings. | Existing bookings can still be disrupted; no guarantee or automatic replacement/cancellation. |
| Owner unavailable blocks | Owners can keep dates for themselves. | Cannot override committed dates; first cancel the reservation or complete the active return. |
| Either participant cancels Approved | Releases dates when plans change before handover. | No penalties or formal cancellation dispute process. Active borrows must be returned. |
| Expire on app operations | Closes elapsed, unstarted periods without a job service. | No background notification at midnight; the next operation records expiry. Active borrows never expire. |
| Pause/archive preserves history | Keeps item ownership useful without destroying transaction/chat records. | Cannot edit/pause/archive while commitments exist; restore never reopens old requests. |
| Literal name search + category | Useful for six seeded items; no search infrastructure. | SQLite lowercasing is aimed at the English demo catalogue, not advanced multilingual relevance. |
| Month grid + native date fields | Calendar visualization with a reliable no-JavaScript path. | Browser-native date widgets vary. Server revalidation is always necessary. |
| Borrow-scoped chat and refresh | Simple persistence and participant checks without live infrastructure. | No push, attachments, typing, read receipts, or general inbox. |
| Derived dashboard alerts | Highlights decisions, overdue items, and affected bookings without notification infrastructure. | No unread-event history or push/email delivery. |
| Three selectable members | Demonstrates lending, borrowing, and competing requests quickly. | Not authentication; anyone can select a participant. |
| Backed-up table rebuild | Safely changes the old status constraint while preserving IDs and messages. | Old Approved means Active; original handover timestamps are unknowable. Backups contain the same private demo data as the database. |
| Local-only delivery | No credentials, API keys, or hosted database needed; Windows/macOS commands remain simple. | Loopback URL is not public, and Flask's development server is not production serving. |

## Review alignment

The V1.0 review's Express ZIP audit is a separate implementation. This Flask app has no permissive CORS setup, public reset endpoint, polling interval, or browser-supplied header actor. Existing CSRF, participant checks, escaped content, and saved signing key remain. The demo identity limitation still applies.

The implemented scope combines discovery/detail/search, cancellation, listing controls, overdue alerts, and the user's subsequent calendar requirements. Handover is owner-only, superseding the old approval-as-active shortcut. Retain the original source documents unchanged and describe this app's behavior in the README/design.

## Boundaries

One community, free borrowing, one physical item per listing. No production authentication, hosting, payments, logistics, guarantees, formal disputes, image uploads, condition evidence, reporting workflow, persisted notifications, quantities, waitlists, hourly/recurring bookings, booking amendments/extensions, or external calendar synchronization.

Listing guidance excludes prohibited/hazardous goods, vehicles, credentials, property, services, and hygiene-sensitive personal items. It is guidance, not automatic moderation. Use non-sensitive demo chat; the app does not scan or redact addresses/phone numbers. Keep runtime databases, backups, and signing keys out of GitHub.
