# Campus Commons — decisions and tradeoffs

| Choice | Why it fits this MVP | Tradeoff / limit |
|---|---|---|
| Flask + Jinja | One process, ordinary forms, quick local setup, no JavaScript build chain. | Full page refreshes; richer client interactions would need extra work. |
| SQLite via Python standard library | Durable state without installing a database service. Transactions and partial unique indexes protect the borrow loop. | A single local database and serialized writers; not designed here for multi-instance deployment. |
| Three seeded/selectable members | Amritanshu, Rahul, and Priya show lending, borrowing, and competing requests without sign-up. | Identity selection is not authentication. Anyone can impersonate a demo member. |
| Derive availability from Approved requests | One source of truth prevents mismatched listing/request states. | Catalogue queries check active requests; appropriate for the small demo. |
| Transactional approval and unique index | Availability is rechecked at save time; competing pending requests are rejected atomically. | SQLite lock contention can require retrying; there is no reservation scheduler. |
| One Pending request per borrower/item | Prevent duplicate clicks and confusing duplicate activity. | A borrower must wait for a decision before requesting that same item again. Rejected and returned requests remain history. |
| Fictional contacts after approval | Shows the practical handover step without building chat. | No actual communication, email sending, delivery, or handover verification. |
| Text and local SVG category art | Makes the catalogue readable without upload infrastructure or external image requests. | No individual item photographs. |
| Server-rendered state | Easy to reason about and usable without JavaScript. | Borrower refreshes/navigates to see an owner's decision; no real-time updates. |
| Local-only delivery | Agreed scope keeps setup and the demo reliable without hosting credentials. | The original brief's deployed-URL requirement is deferred. Loopback URLs work on the host machine only. |
| A few integration checks | Covers lifecycle, permission checks, and approval integrity without spending the hackathon on tests. | Not comprehensive browser, load, security, or cross-platform coverage. |

## Date and state simplifications

Borrowing begins on approval. The date is an expected return date, not a future booking window. Today is calculated in Asia/Kolkata; timestamps are stored in UTC. There is no automatic overdue release, expiry job, waitlist, or auto-approval. Requests rejected when another borrower is approved remain rejected after return; members can submit new requests.

Seed data is initialized once. Restarts preserve the catalogue, requests, and signing key. There is intentionally no reset button that could erase demo work by accident.

## Security boundary

CSRF protection, validation, escaped output, and owner checks protect workflow integrity, but the member selector deliberately allows switching to any member. The app does not prove identity. Only fictional emails are seeded; no addresses or phone numbers are collected. Flask's development server is bound to loopback and must not be presented as a production service.

## Deferred features

Authentication, multi-community access, deployment, payments, uploads, search/filters, chat, notifications, reviews, moderation, quantity management, future reservations, logistics, and analytics are outside this build. Production use would first require real authentication, a deliberate hosting/data-access design, operational backups, and appropriate production serving. No implementation of those capabilities is implied by this document.
