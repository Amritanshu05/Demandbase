# Campus Commons — combined-feature demo

Use [STARTUP.md](../STARTUP.md) for macOS/Linux and Windows. Stop the previous app process before restarting. Existing databases migrate automatically with a backup; no reset is required. An optional [local reset](../README.md#reset-the-demo-database) removes reservations, owner blocks, and chat. All members/contacts are fictional.

## Short complete loop — works today

1. Select **Rahul** and create a Sports listing such as “Demo Cricket Bat”. Show it in **My Dashboard / My Items**, then open **Calendar and details**.
2. Select **Amritanshu**. Search `Demo Cricket Bat`, combine Sports, and open the item. Show description, condition, owner, and calendar.
3. Select **today** through a later expected return date. Calendar clicks populate the fields; native date inputs also work. Send the request.
4. Select **Rahul**. Show the incoming Pending request with both dates and approve it. It is now a reservation, not yet an Active borrow.
5. Select Amritanshu. Show **Request approved / Accepted**, the period, Open chat, and expandable fictional owner email. Send a sample handover message.
6. Select Rahul. Reopen chat and reply. Choose **Mark handed over**. This action is available only during the reserved period and only to the owner.
7. Show the item as Lent Out for Rahul and Actively borrowing for Amritanshu. Explore still shows it so others can inspect future availability.
8. Select Rahul and **Mark as returned**. This records the owner's receipt assertion and releases remaining booked dates immediately, even if the return is early.
9. Select Amritanshu. Open **Past requests / View conversation**. Messages remain and sending is read-only. Refresh and restart to show persistence.

If the listing is already booked, use its available dates or create another demo item. A future reservation cannot be handed over early; use today's start date for the short full-cycle demo. The app never verifies that the physical exchange really happened.

## Exact future-calendar example: 1–10 and 20–25

Use a future month (for example December 2026 if it is still in the future). Start/end dates include their boundary days.

1. Open Rahul's available Cricket Bat. As Rahul, block the **15th–17th** in **Owner unavailable dates**.
2. Select Amritanshu and request **1st–10th**.
3. Select Priya and request **20th–25th**.
4. Select Rahul and approve both. Both remain Approved; neither is rejected because the ranges do not overlap.
5. Open the calendar as a borrower: 1–10 and 20–25 are Reserved, 15–17 is Owner unavailable, and other future dates are available.
6. Show an attempted **10th–12th** request conflicts; **11th–14th** is free. Boundaries are inclusive.
7. Show that Pending requests do not reserve anything; approval declines only overlapping Pending requests, not separate periods.
8. During the first booked period, Rahul can mark handover. After confirming return, he can start the next borrow when its own period begins.
9. An unstarted reservation expires after its end date. An Active borrow is never automatically returned.

## Cancellation and late returns

- Borrowers can cancel their Pending requests. Either participant can cancel an Approved reservation before handover, freeing dates. An approved conversation stays as read-only history.
- Active borrowing cannot be cancelled; only the owner can record return.
- If Active borrowing is still unreturned after its due date, show Overdue and dashboard alerts. New requests/approvals are blocked; existing future reservations stay with late-return warnings. The next handover is refused until the earlier item returns.
- No penalties, auto-return, auto-release, or silent cancellation of future approvals occur.
- The integration checks exercise late/expired dates using isolated fixed clocks. There is no user-facing clock control and no need to change your computer's date for the demo.

## Listing management and privacy

1. With no Approved/Active commitments, edit an owned listing's name/description; show search results update.
2. Pause it through the confirmation screen. Pending requests are declined with a reason; the item disappears from Explore. Resume offers its free dates again.
3. Archive it and show its history in **Archived items**. Restore it; old requests stay closed.
4. Show that another member cannot edit or manage the calendar. Approved/Active commitments lock edit/pause/archive, and owner blocks cannot override booked dates.
5. Open a borrow chat while selected as Priya when she is not a participant: access is denied. Calendar free/busy information does not expose transaction details.

Identity switching is intentionally available to any demo visitor. Participant checks protect the selected-member workflow, not authenticated private messaging.

## Focused verification

macOS / Linux:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Windows PowerShell / Command Prompt:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Thirteen integration checks use temporary databases, including concurrent approval, date boundaries, blocks/controls, cancellation/expiry, overdue/early return, chat, and real legacy migration/rollback. Browser QA also checks calendar selection across months, disabled dates, end-to-end UI actions, and desktop/mobile widths. Your normal demo database is not used for verification.
