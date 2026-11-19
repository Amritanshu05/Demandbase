# Community Resource Sharing Platform
## Product Strategy, MVP Redesign, Requirements & System Design Review

**Document version:** 1.0  
**Review date:** 19 November 2026  
**Inputs reviewed:**
- `Community_Resource_Sharing_MVP_v0.3.md`
- `DEMANDBASEE_amrit_v1.zip` (v0.1 specification, Node.js/Express application, SQLite database, frontend and verification script)

**Purpose:** Turn the current MVP proposal into a coherent product definition and a defensible system-design baseline. This is a planning and design document; it does not claim that the proposed changes have been implemented.

---

# 1. Executive assessment

The current product has a sound, demonstrable core:

> A member lists an underused physical item, another member requests temporary access, the owner decides, both members coordinate, and the item is eventually returned.

The v0.3 document improves the earlier v0.1 scope by adding a personal inventory dashboard and a borrow-specific chat. Those are useful additions because they make the two sides of a borrowing arrangement visible.

However, the current proposal is still closer to a **borrow-request tracker** than a complete resource-sharing product. The main gaps are not more screens or advanced technology. They are the rules and safeguards around the real-world lifecycle:

- What exactly does “approved” mean: permission granted, or item physically handed over?
- What happens if the borrower changes their mind?
- What happens when the return date passes?
- How do both parties agree on the item's condition?
- What happens if the item is unavailable, damaged, lost, or the owner stops sharing it?
- How does a member know whether a listing is trustworthy and genuinely available?
- How are identity and permissions enforced outside a demo environment?

These questions should shape the product and data model before adding sophisticated features.

## 1.1 Recommended product direction

**Build a community-first, free, peer-to-peer borrowing platform for movable physical items.**

The platform should support the full digital lifecycle:

1. A member publishes an item they are willing to lend.
2. Another member discovers it and submits a request for a proposed borrowing period.
3. The owner approves or declines.
4. Both parties can confirm the handover and record the item's condition.
5. The active borrowing is tracked, including the expected return date.
6. The return is confirmed and the item becomes available again.
7. The borrowing record remains available as history.

The app records agreements and status. It does not physically transfer, inspect, insure, deliver, or guarantee the item.

## 1.2 What not to build

For the hackathon MVP, do not build:

- Payments, deposits, subscriptions, wallets, refunds or monetisation.
- Delivery, pickup allocation, courier tracking, maps or route planning.
- Insurance, guarantees, damage claims or formal dispute adjudication.
- Microservices, Kafka, Redis, complex search infrastructure or a recommendation engine.
- A general-purpose social network or general-purpose messaging product.

These exclusions are sensible. They keep attention on the actual product problem.

---

# 2. What the existing documents and code tell us

## 2.1 v0.3 specification: what is already good

The following decisions are strong and should mostly remain:

| Existing decision | Assessment | Recommendation |
|---|---|---|
| One predefined demo community | Reduces scope and makes the demo understandable | Keep for hackathon; model community membership conceptually for future growth |
| Physical, movable goods only | Clear product boundary | Keep |
| Free borrowing | Avoids commerce complexity | Keep |
| One listing = one physical item | Avoids inventory quantity complexity | Keep |
| Owner approval required | Preserves owner control | Keep |
| Expected return date | Makes borrowing trackable | Keep, but add overdue status |
| Borrow-specific chat | Correctly scopes communication to a real transaction | Keep minimal |
| Personal inventory dashboard | Useful for both roles | Keep |
| Relational database | Appropriate for ownership and lifecycle relationships | Keep |
| Modular monolith | Appropriate for a small product | Keep |

The v0.3 document correctly avoids premature infrastructure. A single application and relational database are enough for the proposed scale.

## 2.2 Gaps in the v0.3 product definition

### A. Approval and physical handover are conflated

The current model changes the listing to `Borrowed` immediately when the owner approves the request.

That is simple, but approval does not necessarily mean the borrower has received the item. The two people may never complete the handover.

**Recommendation:** Distinguish permission from physical custody.

For the improved lifecycle:

- `Approved` means the owner has agreed to lend the item.
- `Active` means both parties have confirmed that the item was handed over.
- `Returned` means the owner has confirmed receipt of the item back.

If the one-hour demo cannot support handover confirmation, retain the simpler approval-to-active shortcut, but label it honestly as a demo simplification. Do not describe approval as proof of physical handover.

### B. No cancellation path

The borrower can request, but the requirements do not define what happens if they change their mind. The owner also has no defined way to withdraw an approval before handover.

**Recommendation:**

- Borrower may cancel a `Pending` request.
- Owner may reject a `Pending` request.
- Either party may request cancellation of an `Approved` but not-yet-handed-over borrowing.
- Once the item is confirmed as handed over, cancellation is no longer the same operation; it should use the return process.

For the hackathon, implement borrower cancellation of pending requests first. Keep approved-before-handover cancellation as a documented follow-on if time is tight.

### C. No overdue state

The expected return date is stored but never changes the product experience.

**Recommendation:** Derive an overdue indicator when the current date is later than the expected return date and the borrow is still active.

Do not automatically mark an item as returned or release it. An overdue date is a reminder/status, not proof that the item has been returned.

### D. No condition evidence

The item has a condition field on its listing, but that is not enough to describe its state at the time of a particular handover and return.

**Recommendation:** Add a lightweight condition record at handover and return:
- Condition label: excellent / good / fair / damaged.
- Optional short note.
- Optional photo in a later version.

For a strict one-hour build, use condition labels and notes only, or defer this to P1. Do not build image storage just to claim condition management.

### E. No listing lifecycle controls

The owner can create an item, but the product does not define editing, pausing, archiving, or deleting a listing.

**Recommendation:**
- Owner can edit listing details while it is not actively borrowed.
- Owner can mark an available listing as `Paused` or `Archived`.
- Owner cannot delete a listing with borrowing history; archive it instead.
- A listing cannot be approved for borrowing when paused or archived.

This avoids destroying history and makes owner control more realistic.

### F. No clear discovery strategy

A small seeded demo can browse a list, but a resource-sharing product needs a way to find relevant items.

**Recommendation for MVP:** Search by item name and filter by category. Do not add maps or geolocation yet.

For a single community, category and text search provide meaningful value without location permissions, map APIs or ranking infrastructure.

### G. No notification model

The dashboard is useful only if members remember to check it.

**Recommendation:** In-app notification indicators for:
- New borrowing request received.
- Request approved or declined.
- Borrower cancelled a request.
- Return date approaching or overdue.
- Item marked returned.

For the hackathon, a pending count and dashboard alert are sufficient. Push, email and SMS are out of scope.

### H. No reporting or moderation boundary

Even a small community can have inappropriate listings or unsafe use cases.

**Recommendation:** Include a simple `Report listing` / `Report member` action in the product design. For the one-hour MVP, it can be a visible placeholder or a basic persisted report record only if the core flow is already stable.

Do not imply that a report button provides a full moderation or dispute-resolution system.

---

# 3. 10,000-foot product view

## 3.1 The product is not just a catalogue

The product has four connected domains:

1. **Community:** Who is allowed to participate and which members can see each other.
2. **Resources:** What is being shared, who owns it, its condition and whether it is lendable.
3. **Borrowing:** The request, decision, handover, active use and return lifecycle.
4. **Trust and accountability:** Identity, permissions, records, communication and reporting.

A design that only optimises the catalogue will miss the hardest part: managing temporary access between people.

## 3.2 Product principles

Use these principles to evaluate every proposed feature:

1. **Owner control:** The owner decides whether and when to lend an item.
2. **Clear availability:** Never show an item as requestable when it cannot be approved.
3. **Explicit consent:** A request is not a booking; approval is not physical handover.
4. **Traceable lifecycle:** Important actions have timestamps and participants.
5. **Minimum necessary data:** Do not collect exact home addresses, identity documents or contact details without a real need.
6. **Community before marketplace:** The first version serves a bounded group, not the entire internet.
7. **Safe defaults:** Exclude illegal, dangerous, regulated or inappropriate resource categories.
8. **Simple failure handling:** Every action should have a clear success or failure result.
9. **History over deletion:** Preserve borrowing records; archive listings rather than erasing their history.
10. **No premature scale engineering:** Use the simplest architecture that preserves correctness and can be explained.

## 3.3 Recommended initial target audience

For a hackathon demo, choose **one college/campus or one bounded community**.

Why:
- Members have a plausible reason to trust a shared community identity.
- Common use cases are easy to demonstrate: calculator, cricket bat, books, charger, drill, tripod, sports equipment.
- A bounded community makes discovery useful without building maps or location search.
- Judges can understand the product in one sentence.

Do not claim the product is already suitable for a public, city-wide marketplace. That requires stronger identity, safety, moderation, abuse prevention and availability handling.

## 3.4 Product positioning

Suggested one-line positioning:

> Borrow what your community already owns. Share what you are not using.

Suggested problem statement:

> People often buy or go without items they need only occasionally, while useful items owned by nearby community members sit unused. The platform makes those underused resources discoverable and gives members a simple, accountable way to lend and borrow them temporarily.

---

# 4. Recommended resource scope and safety boundary

The original statement says “any resource”. That is a vision, not a safe MVP definition.

## 4.1 Resource taxonomy

| Resource class | MVP decision | Reason |
|---|---|---|
| Books and study material | Include | Low complexity and easy to demonstrate |
| Sports equipment | Include | Strong community use case |
| Tools and DIY equipment | Include with safety caveat | Useful, but some tools can be hazardous |
| Electronics and accessories | Include | Common temporary need |
| Cameras and creative equipment | Include | Clear high-value use case; condition records matter |
| Kitchen and household items | Include selectively | Common but hygiene-sensitive categories need rules |
| Clothing and personal-use items | Exclude initially | Hygiene and fit concerns |
| Vehicles | Exclude | Insurance, licensing, safety and legal complexity |
| Rooms, property and facilities | Exclude | Access control, liability and scheduling complexity |
| Services and skills | Exclude | Not physical inventory; different product model |
| Digital subscriptions/accounts | Exclude | Credential sharing and terms-of-service risks |
| Weapons, hazardous materials and illegal goods | Prohibit | Safety and legal risk |

**Recommendation:** Keep the MVP to ordinary movable goods. Add a prohibited-items policy even if the first demo only uses seeded safe examples.

## 4.2 Item fields

Minimum listing fields:
- Name.
- Category.
- Short description.
- Condition.
- Owner.
- Listing status.
- Created timestamp.

Recommended next fields:
- One cover image.
- Usage notes / handling instructions.
- Optional accessories included.
- Community visibility.
- Last updated timestamp.

Do not add serial numbers, exact home address, identity documents or sensitive owner data to the MVP.

---

# 5. Improved end-to-end product workflow

## 5.1 Main lifecycle

```text
Owner creates listing
        |
        v
     AVAILABLE
        |
        | Borrower submits request
        v
      PENDING
        |
        +--------------------+
        |                    |
     Rejected             Approved
        |                    |
        v                    v
   AVAILABLE        APPROVED / AWAITING HANDOVER
                             |
                             | Both confirm handover
                             v
                           ACTIVE
                             |
                 Due date passes? ---- Yes ---> OVERDUE indicator
                             |
                             | Owner confirms return
                             v
                          RETURNED
                             |
                             v
                         AVAILABLE
```

The `OVERDUE` state should ideally be a derived flag on an active borrow, not a replacement for the active borrowing state. The item remains unavailable while overdue.

## 5.2 Important distinction between states

- **Available:** The owner is willing to receive requests.
- **Pending:** At least one request is waiting for a decision.
- **Approved:** The owner has agreed, but handover has not necessarily happened.
- **Active:** The item has been handed to the borrower and is in their custody.
- **Overdue:** The expected return date has passed while the borrow is still active.
- **Returned:** The owner has confirmed that the item came back.
- **Paused:** Owner temporarily stops new requests.
- **Archived:** Listing is no longer offered but history remains.

Avoid making `Pending` a listing status. It belongs to a request. A listing can remain available while requests are pending, subject to the owner’s policy. For the simplest MVP, allow only one pending request at a time or allow multiple pending requests but only one approval. Pick one rule and explain it consistently.

**Recommended hackathon rule:** Multiple pending requests may exist; the owner approves one; approval atomically rejects the remaining pending requests. This preserves the existing v0.3 behaviour.

## 5.3 Request lifecycle

```text
PENDING
  | \
  |  \ borrower cancels
  |   ---> CANCELLED
  |
  +---- owner rejects ---> REJECTED
  |
  +---- owner approves --> APPROVED
                              |
                              +--> handover confirmed --> ACTIVE
                              |
                              +--> cancelled before handover (future)
```

The MVP may omit a separate handover-confirmation step if the demo deadline requires it. If omitted, document that `Approved` is treated as the active borrow for demo purposes.

## 5.4 Recommended primary user journeys

### Owner journey
1. Open Explore or My Items.
2. Create a listing.
3. Review incoming requests.
4. Approve or decline a request.
5. Open the borrow-specific conversation.
6. Confirm handover (if included).
7. See the active item under Lent Out.
8. See expected return / overdue status.
9. Confirm return.
10. See the item available again and retain the borrowing history.

### Borrower journey
1. Browse or search available items.
2. Open item details.
3. Review description, condition, owner and availability.
4. Submit request with expected return date and optional message.
5. See Pending status.
6. Receive approval or rejection in the dashboard.
7. Coordinate handover in the borrow-specific conversation.
8. See the item under Borrowing.
9. See due date and overdue indicator if applicable.
10. See Returned in history.

### Third-party member journey
1. Browse public-to-community listings.
2. See only the information intended for community discovery.
3. Cannot view private borrowing conversations or private transaction details.
4. Can report a listing or member if reporting is included.

---

# 6. Revised MVP scope

The MVP should prove one complete sharing loop, not imitate every feature of mature rental platforms.

## 6.1 P0 — must-have for a credible MVP

| ID | Requirement | Acceptance criteria |
|---|---|---|
| FR-01 | Demo member selection | At least two seeded demo identities; active identity always visible |
| FR-02 | Browse available listings | Shows available, non-archived listings in the selected community |
| FR-03 | Listing creation | Owner creates item with name, category, description and condition |
| FR-04 | Listing ownership | Every listing has one owner; user cannot edit another member's listing |
| FR-05 | Item detail view | Shows full description, condition, owner and request action |
| FR-06 | Search and category filter | User can find an item by name and narrow by category |
| FR-07 | Borrow request | Member requests an item with expected return date |
| FR-08 | Request validation | Cannot request own item, unavailable item, invalid date or duplicate active/pending request |
| FR-09 | Incoming request dashboard | Owner sees pending requests for owned listings |
| FR-10 | Approve / reject | Only owner can approve or reject a pending request |
| FR-11 | Prevent double borrowing | At most one active borrow per physical listing; approval is atomic |
| FR-12 | Borrower dashboard | Borrower sees outgoing pending, approved, rejected and returned requests |
| FR-13 | Owner inventory dashboard | Owner sees available, paused and lent-out items |
| FR-14 | Return tracking | Owner can mark active borrow returned; listing becomes available atomically |
| FR-15 | Borrow-specific chat | Owner and borrower can exchange plain-text messages for an approved/active borrow |
| FR-16 | Chat authorization | Only the two participants can read or send messages |
| FR-17 | Persistence | Listings, requests, decisions, return status and messages survive refresh/restart |
| FR-18 | Clear status and errors | Every action provides visible success/failure feedback; invalid transitions are rejected |
| FR-19 | Seeded demo data | The app opens with enough realistic listings to explore immediately |
| FR-20 | Demo reset | Reset is available only in a protected development/demo environment, never as a public unauthenticated production endpoint |

**P0 recommendation:** If the hackathon is truly one hour, FR-05 and FR-06 can be simplified to an inline detail panel and basic client-side filtering over the small dataset. Do not compromise server-side permissions or atomic approval to save time.

## 6.2 P1 — important product improvements, not required for the first demo

| Feature | Why it matters | Suggested implementation |
|---|---|---|
| Borrower cancellation of pending request | Prevents stale requests | `Pending → Cancelled` |
| Listing pause/archive | Gives owners control | Owner-only status change |
| Overdue indicator | Makes due dates meaningful | Derived from due date and active status |
| In-app notification indicators | Reduces missed requests and decisions | Dashboard badge and notification list |
| Handover confirmation | Separates approval from actual custody | Both parties confirm |
| Condition at handover and return | Builds accountability | Condition label and short note |
| Listing edit | Keeps information accurate | Owner can edit when not actively borrowed |
| Report listing/member | Basic safety mechanism | Persist report with reason and status |
| Borrowing history | Supports repeat use and accountability | Read-only completed records |
| Listing image | Improves discovery and confidence | One image per listing; only if storage is available |

## 6.3 P2 — later product capabilities

- Multiple communities and community administrators.
- Real authentication and community membership approval.
- Verified member badges.
- Advanced availability calendars and future reservations.
- Waitlists for popular items.
- Multiple units per listing.
- Recommendations and personalised discovery.
- Reviews and reputation scores.
- Push/email notifications.
- Damage/dispute workflows.
- Analytics and community impact reporting.
- Accessibility and localisation enhancements.
- Moderation queues and category-specific safety rules.

Do not mix P1/P2 items into the one-hour implementation unless the core loop is already complete.

## 6.4 Explicit exclusions

Retain the v0.3 exclusions for payments, logistics, insurance, maps/GPS, production identity verification, general messaging, multiple quantities, waitlists, advanced booking calendars, admin dashboards and non-movable resources.

Add these explicit exclusions:
- No guarantee that a borrower will return an item.
- No guarantee of the item's condition or fitness for use.
- No automated penalty or fine for overdue items.
- No automatic release of an overdue item.
- No sharing of personal phone numbers or exact addresses by default.
- No lending of prohibited or dangerous categories.
- No formal dispute adjudication.

---

# 7. Improved non-functional requirements

NFRs should be testable and proportionate. Do not claim production SLAs for a hackathon demo.

| Area | Recommended requirement | How to demonstrate / test |
|---|---|---|
| Correctness | Invalid state transitions are rejected | Try approving a rejected request or returning an already returned borrow |
| Consistency | One physical listing cannot have two active borrows | Submit two approvals concurrently |
| Authorization | Every write/read operation checks the authenticated actor | Try another user's listing action and private chat |
| Privacy | Only community-visible listing fields are public to members; chat is participant-only | Test third-member access |
| Persistence | Core records survive refresh and server restart | Restart and reload |
| Availability | Demo is reachable during judging; graceful error if database is unavailable | Smoke test deployed URL |
| Performance | For a small demo dataset, common reads should normally complete within 2 seconds on a stable connection | Measure Explore and dashboard |
| Usability | Main journey is understandable without verbal instructions | Ask a first-time user to complete it |
| Accessibility | Form controls have labels, keyboard focus and readable contrast | Keyboard-only walkthrough |
| Maintainability | One modular application with explicit domain operations | Inspect route/service boundaries |
| Observability | Server logs unexpected errors and important state transitions | Review logs during demo |
| Data minimisation | Collect only fields required for sharing | Inspect forms and database columns |

### Important security distinction

The demo identity switcher is not authentication. A request header such as `x-user-id` is user-controlled and can be changed by anyone who can call the API.

It is acceptable only for a clearly labelled, non-sensitive hackathon demo with seeded data. It must not be described as secure user authentication.

For any real multi-user deployment:
- Use actual authentication.
- Derive the actor identity from a verified server-side session/token.
- Enforce authorization on the backend/database.
- Never trust a user ID supplied by the browser as proof of identity.
- Keep privileged database keys server-side.

---

# 8. Improved system design

## 8.1 Recommended architecture

For the hackathon: **one frontend + one backend application + one relational database**.

Use a modular monolith. Keep logical boundaries without deploying separate services.

```text
                 Browser / Mobile Web
                          |
                         HTTPS
                          |
                 Frontend Application
                          |
                       REST API
                          |
              Modular Monolith Backend
          _____________|________________
         |             |                |
      Listings      Borrowing          Chat
         |             |                |
         |        Lifecycle Rules       |
         |_____________|________________|
                          |
                   Relational DB
```

Logical backend modules:
- Members / identity.
- Communities (one seeded community in MVP).
- Listings.
- Borrow requests and borrowing lifecycle.
- Messages.
- Notifications (in-app, later).
- Reports (later).

Do not split these into microservices. They share transactions and have a small scale.

## 8.2 Technology decision: reconcile the two documents

There is a mismatch between the current artifacts:

- v0.3 HLD recommends React + Vite, Supabase Postgres and Vercel.
- The ZIP contains a Node.js + Express backend, vanilla HTML/CSS/JS frontend and SQLite via `better-sqlite3`.

These are two different implementation baselines. The team should choose one and update the source-of-truth document. Do not describe the Supabase architecture as implemented in the ZIP.

### Option A — keep the existing Express + SQLite application

**Best when:** The current app already runs and the goal is to improve and demonstrate it quickly.

Advantages:
- Existing routes, UI and database already exist.
- SQLite is simple to run locally and needs no separate database service.
- `better-sqlite3` supports transactions for approval and return operations.
- Minimal migration and setup effort.

Limitations:
- SQLite is best suited to a small demo and modest write concurrency.
- The current demo identity approach is not secure authentication.
- A single local database file needs persistent storage in deployment.
- Scaling to multiple application instances requires a more deliberate shared database strategy.

**Recommendation:** This is the lowest-risk path if the current ZIP is the codebase the team will present.

### Option B — React + Supabase Postgres

**Best when:** The team has already chosen Supabase and can configure it correctly within the available time.

Advantages:
- Managed Postgres and hosted infrastructure.
- Auth and Row Level Security are available.
- Relational constraints and server-side functions can protect lifecycle operations.
- Less custom backend code for a small application.

Limitations:
- RLS must be correctly designed and tested.
- Client-side demo identity switching does not become secure merely because Supabase is used.
- Atomic approval and return should be implemented as database functions/RPC or a trusted server operation.
- A rushed schema/policy setup can create more risk than the existing working app.

### Decision

Do not switch stacks only because one sounds more scalable. Choose the stack that can demonstrate the correct product behaviour reliably.

For the current ZIP, keep Express + SQLite unless the team has a concrete reason and enough time to migrate. If choosing Supabase, revise the implementation and HLD together.

## 8.3 Database model — recommended logical model

The current four-table model is a good start. The following is the next logical design, not a requirement to create every table during the hackathon.

### `users`
- `id`
- `display_name`
- `email` (optional for demo)
- `avatar` (optional)
- `created_at`

### `communities`
- `id`
- `name`
- `created_at`

### `community_members`
- `community_id`
- `user_id`
- `role` (member / moderator, later)
- `status` (active / pending / suspended, later)
- Unique constraint on `(community_id, user_id)`

For a one-community demo, this can be seeded and simplified.

### `listings`
- `id`
- `community_id`
- `owner_id`
- `name`
- `category`
- `description`
- `condition`
- `status` (`available`, `paused`, `archived`)
- `created_at`
- `updated_at`

Do not store `borrowed` as an independent truth if it can be derived from an active borrow. If retained for query convenience, update it in the same transaction as the borrow record and enforce consistency.

### `borrow_requests`
- `id`
- `listing_id`
- `borrower_id`
- `expected_return_date`
- `status` (`pending`, `approved`, `rejected`, `cancelled`, `active`, `returned`)
- `created_at`
- `decided_at`
- `approved_at`
- `handed_over_at` (nullable)
- `returned_at` (nullable)
- `cancelled_at` (nullable)

For the simplified v0.3 implementation, `approved` can be treated as active. The separate `active` state is recommended when handover confirmation is added.

### `messages`
- `id`
- `borrow_request_id`
- `sender_id`
- `body`
- `created_at`

The borrow request can identify the two participants, so a separate conversation table is unnecessary for one conversation per borrowing.

### `condition_records` (P1)
- `id`
- `borrow_request_id`
- `recorded_by`
- `stage` (`handover`, `return`)
- `condition`
- `note`
- `created_at`

### `notifications` (P1)
- `id`
- `recipient_id`
- `type`
- `related_entity_id`
- `read_at`
- `created_at`

### `reports` (P1/P2)
- `id`
- `reporter_id`
- `reported_user_id` (nullable)
- `listing_id` (nullable)
- `reason`
- `status`
- `created_at`

## 8.4 Important database constraints

At minimum:
- Foreign keys for owner, borrower, listing and sender.
- `NOT NULL` for required fields.
- Check constraints for allowed status values.
- Index `listings(status, category, created_at)`.
- Index `borrow_requests(listing_id, status)`.
- Index `borrow_requests(borrower_id, created_at)`.
- Index `messages(borrow_request_id, created_at)`.
- Ensure at most one active borrow per listing.

For PostgreSQL, a partial unique index can enforce one active borrow per listing. For SQLite, use a partial unique index if the selected SQLite version supports it, or use a transaction with a guarded conditional update and verify the affected row count.

Example conceptual constraint:

```sql
CREATE UNIQUE INDEX one_active_borrow_per_listing
ON borrow_requests(listing_id)
WHERE status IN ('approved', 'active');
```

Adapt the allowed active states to the final lifecycle model. Do not copy this constraint unchanged if `approved` is not considered an active borrow in the selected implementation.

## 8.5 Atomic approval

The approval operation is the most important consistency boundary.

It should:
1. Load the request and listing.
2. Verify the actor is the listing owner.
3. Verify the request is still pending.
4. Verify the listing is still available.
5. Change the selected request to approved.
6. Change the listing availability consistently.
7. Reject competing pending requests for the same listing.
8. Commit all changes together.

If any check fails, roll back the whole operation.

Never implement this as separate uncoordinated frontend writes.

## 8.6 Atomic return

The return operation should:
1. Verify the actor is the owner.
2. Verify the borrow is active.
3. Mark the borrow returned.
4. Record the return timestamp.
5. Release the listing.
6. Commit all changes together.

Do not release a listing if the borrow update failed.

## 8.7 API design

Suggested REST operations:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/listings` | Browse available listings |
| GET | `/api/listings/:id` | View item details |
| POST | `/api/listings` | Create listing |
| PATCH | `/api/listings/:id` | Edit or pause/archive own listing |
| POST | `/api/listings/:id/requests` | Request to borrow |
| GET | `/api/me/dashboard` | Current member's inventory and borrowing |
| GET | `/api/requests/:id` | View request details |
| POST | `/api/requests/:id/approve` | Approve request |
| POST | `/api/requests/:id/reject` | Reject request |
| POST | `/api/requests/:id/cancel` | Cancel own pending request |
| POST | `/api/borrows/:id/return` | Confirm return |
| GET | `/api/borrows/:id/messages` | Read private borrow chat |
| POST | `/api/borrows/:id/messages` | Send chat message |

The endpoint names can differ from the existing code. Consistency and server-side authorization matter more than exact naming.

## 8.8 Chat design

Keep chat deliberately small:
- One conversation per borrowing.
- Plain text only.
- Only owner and borrower can read/send.
- Messages ordered by timestamp.
- Maximum message length.
- Escape user content on rendering.
- Returned conversations are read-only.
- No attachments, typing indicators, read receipts, group chat or WebSockets in MVP.

Polling every few seconds is not essential. Fetch messages when opening the chat and provide a manual refresh. Add polling only if it materially improves the demo and does not create duplicate requests or timer leaks.

---

# 9. Review of the supplied implementation ZIP

This is a source-level review of the files included in the ZIP. It is not a claim that the application was executed or that the verification script passed in this review.

## 9.1 What the implementation already demonstrates

The ZIP contains:
- Node.js and Express.
- `better-sqlite3`.
- A vanilla JavaScript frontend.
- SQLite tables for users, listings, borrow requests and messages.
- Seeded demo users and items.
- Listing creation and browsing.
- Borrow request creation.
- Owner approval and rejection.
- Return action.
- Borrow-specific chat.
- Dashboard data.
- A scripted HTTP verification flow.

The code uses a SQLite transaction for approval and return, which is directionally correct. The test script attempts to verify the end-to-end journey and unauthorized chat access.

## 9.2 Important implementation risks to fix

### Critical: demo identity is spoofable

The server reads the user ID from `x-user-id` or a query parameter. Anyone who can call the API can impersonate another seeded member.

**Fix:** Keep this only for the local/hackathon demo and label it as a demo-only identity mechanism. For a public multi-user deployment, use real authentication and derive the user ID from the verified session.

### Critical: public database reset route

The ZIP exposes `POST /api/reset` without an apparent authentication or environment guard.

**Fix:** Disable this route in production. In a demo environment, protect it with a secret or keep it available only through a local development script.

### High: permissive CORS

The server uses `cors()` with default permissive behaviour.

**Fix:** Restrict allowed origins to the deployed frontend origin when deploying. CORS is not authentication, but it should not be unnecessarily open.

### High: listing state and borrow state can drift

The application stores a listing status and a borrow request status separately.

**Fix:** Keep all transitions transactional, check affected row counts, and add a database-level one-active-borrow constraint. Consider deriving `Borrowed` from the active borrow record rather than treating both records as independent truths.

### High: handover semantics are ambiguous

Approval changes the listing to Borrowed even though the physical exchange happens outside the app.

**Fix:** Either introduce handover confirmation or explicitly state that the MVP treats approval as the start of borrowing for demonstration purposes.

### High: input validation needs tightening

The visible routes validate several required fields and dates, but the design should also enforce:
- Maximum lengths for item name, description and message.
- Allowed categories and condition values.
- Strict date parsing in a consistent timezone.
- Rejection of malformed JSON and unexpected types.
- Consistent API error shapes.

### High: no rate limiting / abuse controls

A public endpoint can be spammed with requests or messages.

**Fix:** For a real deployment, add rate limits to request and message creation. This is not necessary for a closed, seeded demo.

### Medium: no pagination

Explore and dashboard operations currently fit a small seeded dataset.

**Fix:** Add pagination when the dataset becomes large. Do not build it prematurely for a handful of demo records.

### Medium: no listing edit/archive lifecycle

The specification does not define these operations.

**Fix:** Add owner-only edit and archive/pause in a later iteration.

### Medium: no overdue handling

The database records an expected date but the product does not surface overdue status.

**Fix:** Derive overdue state in dashboard responses or UI; do not automatically release the item.

### Medium: polling and chat lifecycle

The frontend starts a polling interval while chat is open.

**Fix:** Ensure the interval is always cleared on close, identity switch and component teardown. Prevent overlapping fetches if a request takes longer than the polling interval. A manual refresh is enough for the demo.

### Medium: tests are mostly a happy-path script

The test script covers the main lifecycle and a third-party chat access attempt, but it does not establish coverage for all edge cases. The printed final success message should only be trusted if every assertion is actually checked and failures cause a non-zero exit.

**Add tests for:**
- User cannot request their own listing.
- Invalid and past dates are rejected.
- Duplicate pending request is rejected.
- Owner cannot approve another owner's request.
- Borrower cannot approve their own request.
- Two simultaneous approvals cannot both succeed.
- Rejected/cancelled requests cannot be approved later.
- Returned borrow cannot be returned twice.
- Non-participant cannot read or send chat.
- Chat cannot be sent after return.
- Archived/paused listing cannot be requested.
- Database reset is unavailable in production.

## 9.3 Important documentation mismatch

The v0.3 document recommends Supabase/Postgres, while the ZIP is Express/SQLite. This is not automatically a technical flaw, but it is a documentation and decision-traceability flaw.

The final project presentation should say exactly which stack is in the running demo and why it was chosen. Keep proposed future architecture separate from implemented architecture.

---

# 10. Product features that create meaningful differentiation

These are not all MVP features. They are ideas worth evaluating from the 10,000-foot product perspective.

## 10.1 Trust layer

**Problem:** A user is lending a personal possession to another person. They need confidence about who is requesting it and what happens if something goes wrong.

Possible features:
- Verified community membership.
- Member profile with borrowing history.
- Two-way reviews after return.
- Condition records at handover and return.
- Report listing/member.
- Clear prohibited-items policy.

**Priority:** High product importance; implement gradually. Real identity verification and dispute resolution are not one-hour MVP features.

## 10.2 Availability and reservation layer

**Problem:** A resource may be listed but unavailable during the time the borrower needs it.

Possible features:
- Availability calendar.
- Request start date and end date.
- Owner-defined blackout periods.
- Waitlist for popular resources.
- Automatic expiry of stale pending requests.

**Priority:** Medium. For the current MVP, one expected return date and owner approval are enough. A full calendar introduces scheduling conflicts and more complex overlap rules.

## 10.3 Resource condition and accountability

**Problem:** The owner and borrower may disagree about an item's condition.

Possible features:
- Condition at listing.
- Condition at handover.
- Condition at return.
- Notes and photos.
- Both-party acknowledgement.

**Priority:** Condition label and note are valuable next steps. Photo evidence is later.

## 10.4 Community discovery

**Problem:** A large catalogue is useless if members cannot find what they need.

Possible features:
- Search by name.
- Category filters.
- Recently added.
- Popularly requested.
- Saved items.
- “Request an item” post when no listing exists.

**Priority:** Basic search and category filters are P0. Saved items and request posts are later.

## 10.5 Community impact

The platform's broader value is reducing idle resources and unnecessary purchases.

Possible metrics:
- Number of items shared.
- Number of completed borrows.
- Repeat borrowers/lenders.
- Most-used categories.
- Estimated purchases avoided (only if measured transparently).

**Priority:** A simple demo impact counter can be useful for judging, but do not invent carbon savings or monetary savings without a defensible methodology.

## 10.6 “Request something not listed” feature

A borrower may need an item that nobody has listed yet.

Potential flow:
1. Member posts a wanted item.
2. Community members see the request.
3. Someone who owns it can respond or create a listing.
4. The normal borrowing flow begins.

This can improve marketplace liquidity, but it adds a second content type and notification workflow.

**Recommendation:** Keep it as a strong P2 idea, not part of the initial MVP.

---

# 11. Design decisions and trade-offs to defend in judging/interviews

| Decision | Chosen approach | Alternative | Why this is reasonable now | When to revisit |
|---|---|---|---|---|
| Architecture | Modular monolith | Microservices | Shared lifecycle transactions; tiny team and dataset | Independent scaling or organisational boundaries |
| Database | Relational SQL | NoSQL document store | Ownership, requests, messages and status transitions are relational | Only if access patterns genuinely require another store |
| Borrow approval | Owner-controlled | Instant booking | Protects owner autonomy and avoids accidental commitments | When availability calendars are reliable |
| One physical item per listing | Single-unit listing | Quantity inventory | Simpler consistency and demo | Shared equipment pools or libraries |
| Chat | Borrow-specific text chat | General chat platform | Conversation has a clear business context | If users need broader community messaging |
| Availability | Owner approval + expected return date | Full booking calendar | Less scheduling complexity | When date overlap becomes a major use case |
| Search | SQL text/category filter | Dedicated search engine | Small catalogue | Large catalogue or advanced relevance needs |
| Notifications | Dashboard indicators | Push/email/SMS | Lowest infrastructure and permission burden | When members miss important events |
| Identity | Seeded demo switcher | OAuth/authentication | Hackathon demonstration only | Before real public users |
| Item media | Seeded image/icon or one optional image | Multi-image object storage | Reduces implementation work | When listing quality/discovery needs it |
| Deployment | One application deployment | Distributed services | Easy to demo and operate | Only with measured need |

## 11.1 Why relational database is the right default

The core data has strong relationships:
- A listing belongs to an owner.
- A request belongs to a listing and a borrower.
- An approved request creates an active borrowing relationship.
- A message belongs to a borrow request and a sender.

Correctness matters more than schema flexibility. SQL transactions and constraints are valuable for preventing double borrowing and invalid transitions.

## 11.2 Why not Redis or Kafka?

The MVP does not have:
- High-volume asynchronous event processing.
- A large notification fan-out.
- Heavy caching requirements.
- Independent services that need a message broker.

A relational database and normal HTTP requests are enough. Adding Redis or Kafka would increase setup and operational complexity without solving a current problem.

## 11.3 Why not WebSockets?

Chat volume is low and real-time delivery is not central to proving the sharing lifecycle. Fetch-on-open/manual refresh is enough. Polling can be added if the demo benefits.

Use WebSockets later only if real-time interaction becomes a genuine product requirement.

## 11.4 Why no geolocation initially?

A bounded community and category/text discovery can demonstrate the product without collecting precise location. Location adds permission UX, privacy implications, map dependencies and distance ranking.

If the product later serves a city, consider coarse area/neighbourhood discovery before exact coordinates.

---

# 12. UI and UX recommendations

The current three-area layout is a reasonable starting point. Improve information hierarchy rather than adding many screens.

## 12.1 Recommended navigation

- **Explore** — discover items.
- **My Activity** — requests, active borrowing and history.
- **My Items** — items I own, including lent-out items.
- **Create Listing** — prominent action.

For a very small demo, My Items and My Activity may remain one dashboard with clear sections.

## 12.2 Listing card should answer four questions

1. What is the item?
2. What condition is it in?
3. Who owns it?
4. Can I request it?

Show:
- Item image/icon.
- Name.
- Category.
- Condition.
- Owner display name.
- Availability.
- Request action.

Do not show phone number or precise address on a public card.

## 12.3 Dashboard should make next actions obvious

Owner:
- Pending requests needing a decision.
- Items currently lent out.
- Items available / paused.
- Overdue items needing attention.
- Recent returned items.

Borrower:
- Pending requests.
- Approved / active borrows.
- Due soon / overdue.
- Returned history.

Use clear status labels and avoid relying only on colour.

## 12.4 Important UX details

- Disable duplicate submit while a request is being sent.
- Confirm destructive actions such as archive.
- Explain why an item cannot be requested.
- Show the expected return date in a human-readable format.
- Distinguish “Request sent” from “Request approved”.
- Distinguish “Approved” from “Handed over” if the handover state exists.
- Make empty states helpful: “No items yet — list something you are not using.”
- Preserve form values when a recoverable server error occurs.
- Show loading and failure states rather than blank screens.

---

# 13. Hackathon demo strategy

The demo should prove the product, not just show screens.

## 13.1 Recommended 3-minute demo

**0:00–0:20 — Problem**
- Show a few common items.
- Explain that many resources sit unused while others need them temporarily.

**0:20–0:50 — Owner creates listing**
- Select Member A.
- Create a cricket bat or calculator listing.
- Show it in Explore.

**0:50–1:20 — Borrower requests**
- Switch to Member B.
- Search/filter the item.
- Open details and request it with a return date.

**1:20–1:50 — Owner approves**
- Switch to Member A.
- Show incoming request.
- Approve it.
- Show that the item is no longer available to another borrower.

**1:50–2:20 — Both sides**
- Show Member A's Lent Out section.
- Show Member B's Borrowing section.
- Open borrow-specific chat and exchange a message.

**2:20–2:45 — Return**
- Mark the item returned.
- Show it available again.
- Show history remains.

**2:45–3:00 — Design decisions**
- Explain why one community, free borrowing, owner approval, SQL transactions and a modular monolith were chosen.
- State what is deliberately excluded.

## 13.2 What judges should be able to see

- Real persistence, not just static mock cards.
- Two different user perspectives.
- Owner-only approval.
- Prevention of double borrowing.
- Borrower/owner dashboard consistency.
- Private borrow-specific chat.
- Return and re-availability.
- Honest explanation of demo-only identity and out-of-scope logistics/payments.

## 13.3 Demo failure fallback

- Seed realistic sample data before judging.
- Keep a known-good demo account and reset procedure.
- Do not rely on a live external service for the core workflow.
- If chat fails, preserve the listing/request/approval/return lifecycle.
- If the deployment is unavailable, have a local fallback ready if the judging rules allow it.

---

# 14. Prioritised implementation plan

If the build window is one hour, use this order:

| Order | Work | Must remain correct |
|---|---|---|
| 1 | Database seed and app boot | App loads reliably |
| 2 | Explore and create listing | Owner association and validation |
| 3 | Request to borrow | Own-item and duplicate checks |
| 4 | Owner request dashboard | Correct owner sees request |
| 5 | Atomic approve/reject | No double borrowing |
| 6 | Owner/borrower dashboard | Both views agree |
| 7 | Return action | Borrow and listing update atomically |
| 8 | Basic chat | Participant-only access |
| 9 | Search/category filter | Useful discovery |
| 10 | Final smoke test and demo rehearsal | Full journey works after refresh |

If time is extremely tight, defer advanced chat refresh, condition evidence, notifications and listing editing. Do not defer state integrity, ownership checks or persistence.

---

# 15. Test strategy

A credible MVP needs more than one happy-path demo.

## 15.1 Core functional tests

- Member A can create a listing.
- Member B can see an available listing.
- Member B can request it.
- Member A can see the incoming request.
- Member A can approve it.
- Member B sees approved status.
- Item disappears from available Explore.
- Owner sees item as lent out.
- Borrower sees item as borrowed.
- Owner marks item returned.
- Item becomes available again.
- Records survive refresh and restart.

## 15.2 Negative and edge-case tests

- Owner cannot request own item.
- Unknown member cannot create a listing.
- Borrower cannot approve their own request.
- Non-owner cannot approve/reject/return.
- A request cannot be approved twice.
- A rejected request cannot later be approved.
- Two requests cannot both become active for one listing.
- Borrower cannot create duplicate pending requests for the same listing.
- Invalid or past date is rejected.
- A paused/archived listing cannot be newly requested.
- Third member cannot read or send private chat.
- Returned chat is read-only.
- An overdue borrow remains unavailable until returned.
- Public reset is disabled outside demo mode.

## 15.3 Concurrency test

The most valuable system-design test:

Two borrowers submit requests for the same item. The owner (or two concurrent actions) attempts approval around the same time.

Expected result:
- Exactly one active borrowing.
- The other request remains rejected/cannot be approved.
- Listing and request state agree.
- No partial update is visible.

This is the clearest demonstration of why database transactions and constraints matter.

---

# 16. Risks and product assumptions

| Risk / assumption | Why it matters | Mitigation |
|---|---|---|
| Members do not trust each other | Lending involves personal property | Bounded community, member identity, history and condition records |
| Owners do not list enough items | Discovery catalogue becomes empty | Seed demo inventory; later add wanted-item requests |
| Borrowers do not return on time | Owner loses access to item | Due dates, reminders and overdue indicators; no false automatic release |
| Item condition disputes | Trust can break | Handover/return condition records |
| Unsafe items are listed | Physical harm/legal exposure | Prohibited-items policy and reporting |
| Users bypass the app to coordinate | Lifecycle data becomes incomplete | Keep app useful for requests, status and history |
| Demo identity is mistaken for security | Serious privacy risk | Clearly label as demo-only; real auth before public use |
| Scope expands during hackathon | Core flow becomes unreliable | Freeze P0 and defer P1/P2 |
| Technology choice changes late | Integration and deployment risk | Choose one stack and update all docs |

---

# 17. Final recommended product decisions

These are the defaults I recommend adopting unless the team has a strong reason to change them.

| Question | Recommended decision |
|---|---|
| Who is the first audience? | One college/campus or bounded community |
| What can be shared? | Ordinary movable physical goods only |
| Is borrowing free? | Yes, for MVP |
| Who approves? | Resource owner |
| Can one item be borrowed by multiple people simultaneously? | No |
| Can multiple pending requests exist? | Yes; owner approves one, others are rejected |
| Does approval mean physical handover? | Not in the simplified demo; document the limitation |
| Is a full availability calendar needed? | No |
| Is expected return date needed? | Yes |
| Should overdue automatically release the item? | No |
| Is chat needed? | Minimal borrow-specific text chat |
| Are reviews needed? | Later, after a completed borrowing |
| Are condition records needed? | Recommended P1 |
| Is location/GPS needed? | No, not for one community |
| Are payments/logistics needed? | Explicitly no |
| What architecture? | Modular monolith |
| What database? | Relational SQL |
| What should be avoided? | Microservices, Kafka, Redis, WebSockets and complex search in MVP |

---

# 18. Open product decisions for the team

Do not silently assume these are settled. Confirm them before the requirements are frozen.

1. **Target community:** College/campus, residential neighbourhood, workplace, or another bounded group?
2. **Sharing policy:** Strictly free borrowing, or is the broader future vision also to allow paid rentals?
3. **Audience and eligibility:** Can anyone join, or must a member belong to the selected community?
4. **Resource categories:** Which categories are allowed, and which are prohibited?
5. **Handover semantics:** Should owner approval immediately start the borrow in MVP, or should both parties confirm handover?
6. **Cancellation:** Can borrowers cancel pending requests? Can either party cancel after approval but before handover?
7. **Return confirmation:** Is owner-only confirmation sufficient for MVP, or should borrower also acknowledge return?
8. **Condition evidence:** Is a condition label/note enough, or are photos essential?
9. **Discovery:** Is search + category filtering sufficient, or is neighbourhood/distance discovery a core part of the idea?
10. **Trust:** Is demo identity switching acceptable for judging, with a clearly stated limitation?
11. **Implementation baseline:** Are we continuing with the Express + SQLite ZIP, or choosing the proposed React + Supabase architecture?
12. **Time constraint:** Is one hour the actual build limit, or is it only a target for the hackathon demo?

---

# 19. Final recommendation

Do not expand the MVP into a full rental marketplace.

The strongest version of this project is a **community resource-sharing system with a reliable borrowing lifecycle**.

The best design improvements are:

1. Keep the product community-first and free.
2. Add basic search and category filters so resources are discoverable.
3. Make owner approval and one-active-borrow integrity non-negotiable.
4. Clarify the difference between approval and physical handover.
5. Add cancellation and overdue handling to the lifecycle design.
6. Preserve borrowing history instead of deleting records.
7. Add condition records and basic reporting as the next trust improvements.
8. Keep the architecture as a modular monolith with a relational database.
9. Use real authentication before any genuine public deployment.
10. Keep payments, logistics, maps, microservices and real-time chat out of the first MVP.

**The product's success is not measured by how many features it has. It is measured by whether two members can confidently complete a borrowing lifecycle and whether the system's records remain correct throughout it.**

---

# Appendix A — Source alignment and review notes

## A.1 v0.3 specification

The following existing ideas were retained:
- One demo community.
- Physical movable goods.
- Free borrowing.
- Owner approval.
- One physical item per listing.
- Expected return date.
- Minimal borrow-specific chat.
- Personal inventory dashboard.
- Persistent relational data.
- Modular monolith.
- No payments or logistics.

The following were recommended as improvements:
- Search and category filtering.
- Item detail view.
- Cancellation.
- Overdue indicator.
- Listing pause/archive/edit.
- Handover distinction.
- Condition records.
- In-app notification indicators.
- Reporting and prohibited-item policy.
- Stronger authorization requirements.

## A.2 ZIP implementation

The ZIP contains an Express + SQLite implementation, not the Supabase/Postgres stack proposed in v0.3. It includes routes and frontend flows for listings, requests, approval/rejection, return, dashboard and chat, plus a verification script.

The implementation observations in Section 9 are based on source inspection. No claim is made here that the project was run, deployed, penetration-tested or that its test script passed during this review.

## A.3 Terminology

Use these terms consistently across the product and technical interview:

- **Listing:** The published offer of one physical item.
- **Borrow request:** A member's request to temporarily use a listing.
- **Borrowing:** The accepted temporary-use relationship.
- **Owner/lender:** Member who owns the item and decides whether to lend it.
- **Borrower:** Member requesting/using the item.
- **Handover:** Physical transfer of the item from owner to borrower.
- **Return:** Physical return of the item to the owner.
- **Availability:** Whether a listing can receive a new approved borrowing.
- **Overdue:** Expected return date has passed while the borrow remains active.

Avoid using “booking”, “rental” and “borrow” interchangeably if the product is free and owner-approved. Consistent terminology makes the UX, database and interview explanation clearer.
