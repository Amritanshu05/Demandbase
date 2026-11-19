# Community Resource Sharing Platform
## MVP Scope & Functional Requirements

**Document type:** Product source of truth  
**Version:** 0.1 — Draft for scope freeze  
**Date:** 19 November 2026  
**Delivery constraint:** One-hour hackathon implementation (frontend, backend and deployment)  
**Reference product:** Peerby (inspiration for the borrow/request/owner-approval loop; not a feature parity target)

---

## 1. Purpose

This document defines the smallest complete, demonstrable version of the product. It is the source of truth for what the hackathon MVP will and will not do. The subsequent HLD, LLD and technology-selection documents must remain within this scope unless this document is explicitly revised.

The goal is **not** to recreate Peerby or launch a production marketplace. The goal is to demonstrate one useful sharing loop end to end: a member lists an underused physical item, another member discovers it and requests temporary use, the owner approves or rejects the request, and the item can be marked as returned.

## 2. Product definition

**Working name:** Community Resource Sharing Platform

A lightweight community application where members can list physical items they are not currently using and let other members request to borrow those items temporarily, subject to the owner's approval.

**Problem addressed:** People own useful items that sit idle for much of the time, while others in the same community need those items briefly and would prefer borrowing over buying.

**Core value:** Make existing resources easier to discover and temporarily share within a bounded community.

## 3. MVP scope decisions

The following defaults are deliberately chosen to keep the product buildable and demonstrable within one hour. They are implementation assumptions, not claims that every future version must use them.

| Decision | MVP choice | Reason |
|---|---|---|
| Community | One predefined community (use a college/campus label for the demo) | Avoid multi-community setup, geolocation and complex discovery. |
| Resource type | Physical, movable goods only | Clear, demonstrable category; avoids services, skills, digital assets and facilities. |
| Sharing model | Free borrowing; no price field | Keeps the product focused on access, not commerce. |
| User roles | A member can be both owner and borrower | Avoid separate account types and role-management complexity. |
| Identity | Demo member switcher using two seeded users; no sign-up or authentication | Saves time and allows judges to demonstrate both sides. This is a demo-only shortcut, not production security. |
| Approval | Owner must approve each borrow request | Preserves owner control and makes the key workflow visible. |
| Availability | One listing represents one physical item; one active approved borrow at a time | Avoids quantity management and calendar scheduling complexity. |
| Handover | Arranged by the two members outside the application | Explicitly excludes pickup, delivery and logistics. |
| Persistence | Listings and requests are stored in a database | The demo should survive a page refresh and demonstrate a real backend. |

## 4. Users and primary use cases

### 4.1 Owner / lender
A community member who lists an item and decides whether to approve requests for it.

### 4.2 Borrower
A community member who browses available items and requests to borrow one temporarily.

A single person may act as both owner and borrower. The MVP does not create separate account classes.

## 5. Core user journey

1. A member opens the app and selects a demo identity.
2. The member browses the community's available item cards.
3. The member selects an item and submits a borrow request with an expected return date. Borrowing starts when the owner approves.
4. The owner switches to their identity and sees the incoming request in **My Activity**.
5. The owner approves or rejects the request.
6. If approved, the item becomes unavailable to other borrowers while that borrow is active. The borrower can see the approved status.
7. After the item is physically returned (outside the app), the owner marks the borrow as returned. The item becomes available again.

The application records the request and its status; it does not coordinate or verify the physical handover.

## 6. Functional requirements — MVP only

Every requirement below is P0 and must be included for the proposed end-to-end demo. Anything not listed here is out of scope for this one-hour build.

| ID | Requirement | Acceptance condition |
|---|---|---|
| FR-01 | Demo identity selection | Switch between at least two seeded demo members; the selected identity is visible. |
| FR-02 | Browse resources | Explore displays available items with name, category, condition and owner. |
| FR-03 | Create a listing | Create an item with name, category, short description and condition; associate it with the current demo owner. |
| FR-04 | Request to borrow | Request an available item with an expected return date. Borrowing starts on owner approval. |
| FR-05 | View incoming requests | Owner sees pending requests for items they own. |
| FR-06 | Approve or reject | Owner can approve or reject a pending request for their own item. |
| FR-07 | Prevent double approval | Only one request can be active as Approved; approving one request automatically rejects other pending requests for that item. |
| FR-08 | View outgoing requests | Borrower sees submitted requests and current statuses. |
| FR-09 | Mark as returned | Owner marks an approved borrow returned; the item becomes available again. |
| FR-10 | Persist state | Listings, requests and status changes remain after browser refresh. |

### 6.1 Minimal screens

The UI may implement these as pages, tabs or panels; separate page routes are not required.

- **Explore:** available item cards and a create-listing action. Each card shows enough information to request the item without a separate detail page.
- **Request action:** a small form/modal to enter the expected return date.
- **My Activity:** incoming requests for owned items and outgoing requests made by the current demo member; approve, reject and mark-returned actions appear where applicable.
- **Demo identity control:** a visible selector for switching between two seeded members.

No separate item-detail route, search/filter, profile, admin console or chat screen is required.

## 7. Business rules and state model

### 7.1 Listing availability
A listing has one of two states:
- **Available:** a borrower may submit a request.
- **Borrowed:** an approved borrow is active; new requests cannot be approved until return.

### 7.2 Request status
A borrow request has one of four states:
- **Pending:** submitted and awaiting the owner's decision.
- **Approved:** accepted by the owner; the associated listing is locked as Borrowed.
- **Rejected:** declined by the owner; it does not reserve the listing.
- **Returned:** the owner has recorded that the item was returned; the listing becomes Available.

### 7.3 Rules
- A member cannot request their own listing.
- Only the owner of a listing can approve, reject or mark its borrow as returned.
- Only Available listings can receive new requests.
- An item may have only one active Approved request at a time.
- When one request is approved, other pending requests for that item are automatically rejected.
- Approving a request must re-check availability when the action is saved, not rely only on what the UI showed earlier.
- A request must have an expected return date that is today or later. Borrowing begins when the owner approves the request.
- A rejection does not change the listing's availability.
- Marking an approved request as Returned releases the listing.

**Scope simplification:** The MVP captures only an expected return date. It does not implement future start dates, a full availability calendar or multiple future reservations. Approval starts the borrow immediately and reserves the single item until the owner marks it returned.

## 8. Non-functional requirements

These are proportionate to a one-hour hackathon demo, not production service-level commitments.

| Area | MVP expectation |
|---|---|
| Usability | The main flow is understandable without instructions; the primary actions are visible on the relevant screen. |
| Performance | Explore and My Activity should feel responsive with a small seeded catalogue; target under 2 seconds for normal demo requests on a stable connection. |
| Data integrity | A listing must not end up with two active approved borrows. Invalid state transitions must be rejected by the backend. |
| Persistence | A refresh must not erase listings, requests or decisions. |
| Basic access control | The backend must enforce owner-only actions against the selected demo identity. This is a workflow guard only; demo identity selection is not secure authentication. |
| Privacy | Do not collect or display home addresses, phone numbers, precise location or other unnecessary personal data. |
| Input validation | Required fields must be checked; invalid dates and empty item names/descriptions must be rejected with understandable feedback. |
| Deployability | The app must be reachable through one deployed URL for judging. |
| Maintainability | Keep the implementation simple and cohesive; avoid distributed services and infrastructure that do not support the demo. |

## 9. Out of scope

The following are explicitly excluded from this MVP, even if reference platforms provide them:

- Payments, rental fees, subscriptions, deposits, wallet, refunds or monetisation.
- Delivery, pickup scheduling, courier integration, route planning or logistics tracking.
- Insurance, damage guarantees, deposits, formal disputes or claims processing.
- Real identity verification, OAuth, password recovery or production-grade authentication.
- Multiple communities, maps, GPS, distance-based search or location tracking.
- Real-time chat, phone-number exchange, push notifications or email notifications.
- Reviews, ratings, favourites, recommendations or social feeds.
- Image upload, video, document attachments or advanced listing media management.
- Multiple units/quantities per listing, waitlists, future booking windows, recurring bookings or a full availability calendar.
- Search, category filters or a recommendation engine (the demo catalogue is small enough to browse).
- Admin dashboards, moderation workflows, analytics and reporting.
- Services, skills, digital resources, rooms, vehicles or other non-movable/facility resources.

## 10. Demo acceptance checklist

The MVP is considered complete only when the following scenario works against the deployed application:

- [ ] Open the deployed URL and select **Member A**.
- [ ] Create a listing for an item (for example, a laptop or cricket bat).
- [ ] Switch to **Member B** and find the item in Explore.
- [ ] Submit a borrow request with an expected return date.
- [ ] Switch back to **Member A** and see the pending incoming request.
- [ ] Approve the request and show that its status changes for the borrower.
- [ ] Show that the approved item is no longer available for another approval.
- [ ] Mark the item as returned as Member A.
- [ ] Show that the item is Available again.
- [ ] Refresh the page and confirm that the final state persists.

A seeded catalogue should be available before the demo so judges can explore immediately without creating every item from scratch.

## 11. Success criteria

The MVP succeeds if a judge can understand the problem and witness the full temporary-sharing lifecycle without explanation or manual database intervention. The primary success measure is completion of the demo acceptance checklist, not number of features, visual complexity or production readiness.

## 12. Known limitations and assumptions

- The first demo is for one predefined community; the community label can be changed without adding community-management functionality.
- Demo identities are seeded/selectable and do not prove a user's real identity. This limitation must be stated honestly during judging.
- The app tracks the digital request lifecycle but cannot verify that an item was physically handed over, used safely or returned.
- The owner is trusted to record the return accurately.
- Listings use text and category styling rather than uploaded images to save implementation time.
- The backend and database technology are intentionally not selected in this document; that decision belongs in the HLD / technology decision document.

## 13. Scope freeze rule

For the one-hour build, implement only the requirements in Section 6 and the behaviour in Sections 7–8. Do not add a new feature during implementation unless it is necessary to make the core demo flow work. Record additional ideas for a later version instead of expanding this MVP.

## 14. Relationship to the next source-of-truth documents

- **HLD:** will define the chosen architecture, deployment shape, components, data flow and key technology choices needed to satisfy this MVP.
- **LLD:** will define the concrete data model, API contracts, validations, state transitions and UI component behaviour.
- **Technology decisions:** will justify the stack against the one-hour delivery constraint and the MVP's operational needs.

These later documents must trace back to the requirements and exclusions in this MVP document.
