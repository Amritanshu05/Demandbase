# Community Resource Sharing Platform
## MVP Scope, Functional Requirements & Lightweight HLD

**Version:** 0.3 — Minimal in-app chat, personal inventory dashboard and implementation HLD  
**Date:** 19 November 2026  
**Delivery constraint:** One-hour hackathon build (frontend, backend and deployment)  
**Status:** Proposed implementation baseline

## 1. Purpose

This document is the source of truth for the smallest complete, demonstrable product. It adds two capabilities to the earlier MVP: (1) a minimal private chat between the owner/lender and borrower for a specific approved borrowing, and (2) a personal dashboard showing everything the current member owns and lends, plus everything they are borrowing.

The goal remains one end-to-end sharing loop: list an unused physical item, discover it, request it, get owner approval, coordinate handover, use it temporarily, and record its return.

## 2. Product definition

A lightweight community application where members list physical items they are not currently using. Other members can discover those items, request to borrow them, communicate with the owner in a simple item-specific chat after approval, and track the borrowing until return.

**Core value:** Make underused physical resources discoverable and temporarily shareable within one community.

## 3. MVP scope decisions

| Decision | MVP choice | Why |
|---|---|---|
| Community | One predefined demo community | Avoid multi-community and geolocation complexity. |
| Resource type | Physical, movable goods only | Clear and easy to demonstrate. |
| Sharing | Free borrowing; no price field | Excludes commerce. |
| Identity | Two or more seeded demo identities with a visible switcher | Demonstrates both sides without spending time on authentication. |
| Approval | Owner approves or rejects each request | Preserves owner control. |
| Availability | One listing = one physical item; one active borrow at a time | Avoids quantity and calendar complexity. |
| Return date | Borrower supplies expected return date | Enables useful tracking without a booking calendar. |
| Handover | Users arrange physical exchange themselves | No logistics feature. |
| Chat | Minimal text-only, one conversation per approved borrow | Supports handover coordination without building a general messaging product. |
| Persistence | Store listings, borrow requests and messages in a database | State survives refresh and is demonstrably backend-backed. |

## 4. Users

- **Owner/lender:** Lists an item, reviews requests, chats with the approved borrower and confirms return.
- **Borrower:** Discovers an item, requests it, chats with its owner and tracks its expected return.
- Every member can act as both owner and borrower.

## 5. Primary user journey

1. Member A selects their demo identity and lists a cricket bat.
2. Member B discovers the bat and submits a borrow request with an expected return date.
3. Member A sees the incoming request in their dashboard and approves or rejects it.
4. On approval, the item becomes **Borrowed** and is removed from the available-items feed.
5. A private conversation for that borrow becomes available to Member A and Member B only. They use it to agree on handover details.
6. The users meet and exchange the item offline; the app does not arrange delivery or pickup.
7. Member B sees the bat under **Borrowing** with its owner and expected return date.
8. Member A sees it under **Lent Out** with the borrower and expected return date.
9. When the item is physically returned, Member A marks the borrow as returned. The item becomes **Available** again and the transaction moves to borrowing history.

## 6. Functional requirements

All requirements below are P0 for the agreed demo. The implementation should keep screens and interactions minimal.

| ID | Requirement | Acceptance condition |
|---|---|---|
| FR-01 | Demo identity selection | Switch between seeded members; current identity is visible. |
| FR-02 | Browse available resources | Explore shows available items with name, category, condition and owner. |
| FR-03 | Create a listing | Create item with name, category, short description and condition. |
| FR-04 | Request to borrow | Request an available item and provide expected return date. |
| FR-05 | View incoming requests | Owner sees pending requests for their listings. |
| FR-06 | Approve/reject request | Only the listing owner can approve or reject a pending request. |
| FR-07 | Prevent double borrowing | Only one active approved borrow per physical listing. On approval, reject other pending requests for that item. |
| FR-08 | Personal dashboard — owned items | Show all items created by the current member, including Available and Lent Out status. |
| FR-09 | Personal dashboard — borrowing | Show all items the current member has requested/been approved to borrow, including owner and expected return date. |
| FR-10 | Return tracking | Owner can mark an active borrow as Returned; item becomes Available. |
| FR-11 | Borrow-specific chat | After approval, owner and borrower can exchange plain-text messages in a private conversation tied to that borrow. |
| FR-12 | Chat access control | Only the owner and borrower attached to that borrow can read or send its messages. |
| FR-13 | Handover coordination | Chat is used to arrange handover directly; physical exchange remains offline and user-managed. |
| FR-14 | Persist state | Listings, requests, status changes and chat messages survive refresh. |

### 6.1 Minimal UI

Use a single-page application with three primary areas/tabs:

- **Explore:** Available item cards and a small create-listing form.
- **My Dashboard:** Two sections:
  - **My Items / Lent Out:** listings owned by the current member, status, current borrower (if lent), expected return date and pending requests/actions.
  - **Borrowing:** items requested by or actively borrowed by the current member, owner, request/borrow status and expected return date.
- **Borrow Details / Chat:** A simple message list and text input for the owner and borrower of an approved borrow. This can open as a panel/modal from the relevant dashboard row.

A visible demo identity selector allows switching between Member A and Member B. No separate profile or admin screen is needed.

### 6.2 Chat boundaries

- Plain text only; no images, files, voice notes, reactions, typing indicators, read receipts, presence or group chat.
- One conversation per approved borrow request.
- Chat is enabled only after approval and remains readable after return for reference.
- Only the two participants can access it.
- Messages are ordered by creation time and persisted.
- For speed, refresh or a manual refresh button is acceptable; WebSockets are not required for this MVP.
- Do not expose phone numbers or home addresses. Demo contact details may be shown only to the two participants if needed, but chat is the primary coordination mechanism.

## 7. State model and business rules

### 7.1 Listing status
- **Available:** Can be requested.
- **Borrowed:** Has one active approved borrow; cannot be approved for another borrower.

### 7.2 Borrow request status
- **Pending:** Awaiting owner decision.
- **Approved / Borrowed:** Owner accepted; item is currently with borrower (the app trusts users to coordinate the physical handover).
- **Rejected:** Owner declined.
- **Returned:** Owner recorded that the item came back.

### 7.3 Rules
- A member cannot request their own listing.
- Only the owner can approve, reject or mark a borrow returned.
- Only Available listings can be newly approved.
- At most one active approved borrow may exist per listing.
- Approval must re-check availability on the server/database at write time. Use a database transaction and a uniqueness/conditional constraint or row lock so simultaneous approvals cannot double-book an item.
- On approval, other pending requests for the same listing are automatically rejected.
- Expected return date must be today or later.
- Chat is created or made accessible only after approval.
- Only the two participants can access messages; enforce this on the backend for every read and send.
- Marking an approved borrow Returned releases the listing.
- The return action is owner-only in the MVP.
- A returned conversation remains read-only history; no further messages are required after return (recommended simplest rule).

## 8. Non-functional requirements

| Area | MVP expectation |
|---|---|
| Simplicity | One deployable frontend and one backend service; avoid microservices. |
| Data integrity | Backend validates state transitions; no two active borrows for one item. |
| Authorization | Every owner/borrower-specific action is checked server-side, including chat access. |
| Privacy | Chat content visible only to its two participants; do not expose precise addresses or phone numbers. |
| Persistence | Listings, borrow records and messages survive refresh/restart. |
| Performance | Responsive for a small seeded demo dataset; avoid premature caching or queues. |
| Reliability | Show clear errors for failed requests; do not silently claim an action succeeded. |
| Deployability | One public URL; use a managed database or persistent database service. |
| Maintainability | Small modular monolith, clear domain boundaries, environment-based configuration. |

## 9. Explicitly out of scope

- Payments, fees, deposits, subscriptions, wallets, refunds or monetisation.
- Delivery, courier, pickup scheduling, route planning or logistics tracking.
- Insurance, damage claims, formal disputes or guarantees.
- Real authentication/OAuth/identity verification; demo identity switching is not production security.
- Multiple communities, GPS, maps, distance ranking or location tracking.
- General-purpose messaging, group chat, attachments, images in chat, voice/video, read receipts, typing indicators, push/email notifications or WebSockets.
- Reviews, ratings, favourites, recommendations or social feeds.
- Image upload; use seeded images, icons or category placeholders.
- Multiple quantities per listing, waitlists, future booking windows or a full availability calendar.
- Admin console, moderation, analytics or reporting.
- Services, skills, digital resources, rooms, vehicles or non-movable/facility resources.

## 10. Lightweight HLD — recommended simplest effective design

### 10.1 Architecture decision

Use a **modular monolith**: one frontend application, one backend API service and one relational database. Deploy the frontend and backend together if the chosen framework supports it, or deploy the frontend and API as two simple services. Do not use microservices.

```text
Browser (Explore / My Dashboard / Borrow Chat)
                 |
              HTTPS
                 |
        Frontend application
                 |
          REST API routes
                 |
        Backend (one service)
       /        |          \
 Listings   Borrowing    Chat
       \        |          /
          Relational DB
```

### 10.2 Suggested technology choices for one-hour delivery

| Layer | Recommendation | Reason |
|---|---|---|
| Frontend | React + Vite | Fast setup, familiar component model and quick deployment. |
| Styling | Tailwind CSS or existing component library | Fast consistent UI; avoid writing a design system. |
| Backend | Supabase (Postgres + generated REST API) | Removes the need to build and deploy a separate API server under a one-hour deadline. |
| Database | Supabase PostgreSQL | Relational integrity fits users, listings, borrow requests and messages. |
| Data access | Supabase JS client | Direct, simple CRUD for the small MVP. |
| Authorization | Supabase Row Level Security (RLS) policies | Enforce owner/borrower access at the data layer. Demo identity switching must be treated as demo-only; do not expose service-role keys in the browser. |
| Deployment | Vercel for React frontend; Supabase hosted backend/database | Fast path to one public demo URL. |
| Chat updates | Fetch messages when opening chat and manual refresh / short polling only if time allows | Avoid real-time infrastructure; no WebSockets needed. |

**Important demo identity caveat:** A client-side identity selector is not secure authentication. For a public deployment, use Supabase Auth if time permits. If retaining seeded demo identities, keep the demo clearly labelled and restrict the environment/data to non-sensitive sample data. Never put a database service-role secret in frontend code. If RLS cannot be correctly enforced for the chosen demo identity approach, do not claim production-grade privacy/security.

### 10.3 Minimal data model

Use four tables:

**users**
- `id` (primary key)
- `display_name`
- `email` (seeded demo contact; optional)

**listings**
- `id` (primary key)
- `owner_id` (foreign key → users)
- `name`
- `category`
- `description`
- `condition`
- `status` (`available`, `borrowed`)
- `created_at`

**borrow_requests**
- `id` (primary key)
- `listing_id` (foreign key → listings)
- `borrower_id` (foreign key → users)
- `expected_return_date`
- `status` (`pending`, `approved`, `rejected`, `returned`)
- `created_at`
- `approved_at` (nullable)
- `returned_at` (nullable)

**messages**
- `id` (primary key)
- `borrow_request_id` (foreign key → borrow_requests)
- `sender_id` (foreign key → users)
- `body` (plain text, length-limited)
- `created_at`

A separate conversations table is unnecessary: the approved borrow request itself identifies the two participants and acts as the conversation key.

### 10.4 Core backend operations

Whether implemented as Supabase queries or thin API endpoints, keep operations explicit:

- `GET listings` — available listings for Explore.
- `POST listings` — create listing for current member.
- `GET my dashboard` — return owned listings, incoming requests, outgoing requests and active borrow records for current member.
- `POST borrow requests` — create a pending request.
- `POST approve request` — transactionally approve if listing is still available; reject other pending requests; mark listing borrowed.
- `POST reject request` — reject a pending request.
- `POST mark returned` — mark borrow returned and listing available in one transaction.
- `GET messages for borrow` — only for the borrow's owner or borrower.
- `POST message` — only for the borrow's owner or borrower, and only while borrow is active.

### 10.5 Critical consistency and security decisions

1. **Do not trust frontend checks.** The backend/database must validate owner permissions, borrower permissions and status transitions.
2. **Approve atomically.** Update the borrow request and listing in one database transaction; guard against simultaneous approvals. If using Supabase, implement approval/return as Postgres functions (RPC) or another atomic server-side operation rather than multiple uncoordinated browser updates.
3. **Return atomically.** Mark request returned and listing available together.
4. **Scope chat by borrow request.** Every message query must verify that the current user is the owner or borrower for that request. Apply RLS policies to messages and related borrow records.
5. **Never expose secrets.** Frontend may use only public/anon keys protected by RLS; service-role keys stay server-side.
6. **Avoid premature infrastructure.** No Redis, Kafka, WebSockets, microservices, search engine, object storage or background workers are needed for this dataset and deadline.

### 10.6 Development order for the one-hour build

1. Create the database tables and seed two demo members plus sample listings.
2. Build Explore and create-listing UI.
3. Build borrow request and owner approve/reject flow.
4. Build My Dashboard with **My Items**, **Lent Out**, **Borrowing** and expected return dates.
5. Add borrow-specific plain-text chat.
6. Add return action and verify the item becomes available again.
7. Deploy and test the full flow using two demo identities.

If time is running out, preserve the core listing → request → approve → dashboard → return lifecycle first. Chat is the first feature to simplify to a basic persisted message panel, not a reason to compromise the borrow/return integrity.

## 11. Demo acceptance checklist

- [ ] Open the deployed URL and select Member A.
- [ ] Create a cricket bat listing.
- [ ] Switch to Member B and find the bat in Explore.
- [ ] Request it with an expected return date.
- [ ] Switch to Member A and see the incoming request.
- [ ] Approve the request.
- [ ] Confirm the item disappears from available Explore results.
- [ ] Confirm Member A sees the bat under **My Items / Lent Out**, with Member B and the expected return date.
- [ ] Confirm Member B sees the bat under **Borrowing**, with Member A and the expected return date.
- [ ] Open the borrow-specific chat as either participant and send a text message.
- [ ] Confirm a third demo identity cannot access that conversation (if third identity is seeded/tested).
- [ ] Mark the item returned as Member A.
- [ ] Confirm the item is Available again and no longer shown as actively borrowed.
- [ ] Refresh and confirm listings, borrow status and chat messages persist.

## 12. Success criteria and known limitations

The MVP succeeds when a judge can complete and understand the full sharing lifecycle, see both sides' personal inventories and exchange a message tied to a borrow.

Limitations must be stated honestly:
- Demo identity switching is not real authentication.
- Physical handover and condition inspection happen outside the app.
- The app records expected return dates but does not automatically enforce overdue returns.
- Chat is basic text messaging, not a real-time messaging platform.
- The product is a hackathon demonstration, not production-ready marketplace infrastructure.

## 13. Scope freeze and follow-on documents

Implement only the requirements and architecture in this document. Do not add new features during the one-hour build.

The next documents should be derived from this baseline:
- **HLD:** architecture and technology choices are outlined in Section 10; a separate HLD can formalise component/data-flow diagrams and deployment.
- **LLD:** exact SQL schema, RLS policies, RPC/API contracts, validation rules, state transitions and UI component behaviour.
- **Demo script:** a short two-user scenario proving list → request → approve → chat → lent/borrowing dashboard → return.
