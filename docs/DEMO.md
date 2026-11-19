# Campus Commons — hackathon walkthrough

Start the app using [STARTUP.md](../STARTUP.md). For a clean demo, follow the [database reset instructions](../README.md#reset-the-demo-database). All contacts are fictional. Identity selection is a deliberate demo shortcut, not authentication. If an item used below is already borrowed from a previous run, its owner can mark it returned in My Activity, or you can create a new listing.

## List and borrow an item

1. Select **Amritanshu** in the header.
2. Choose **List an item**. Create “Demo Tripod” with category Electronics, condition Good, and a short description.
3. Confirm it appears in Explore with Amritanshu as owner and “Your item · available.”
4. Switch to **Priya**. Find Demo Tripod and choose **Request to borrow**.
5. Select today or a future expected return date and send the request. My Activity shows Pending.
6. Switch to **Amritanshu** and open **My Activity**. Approve Priya's incoming request.
7. Switch to **Priya**. My Activity shows **Request approved**, **Accepted**, Amritanshu's demo contact, and the saved return date. Explain that handover is arranged outside the app.
8. Explore no longer shows Demo Tripod while the Approved borrow is active.
9. Switch to **Amritanshu** and mark it returned. It appears in Explore again; activity shows Returned.
10. Refresh the page, then stop and restart the server. The listing and Returned history remain.

## Show the requested Rahul approval message

1. Select **Amritanshu** and request **Rahul's Cricket Bat**.
2. Choose a future return date. Selecting 22 November in the current year produces the example date when that date has not passed; otherwise use another valid date.
3. Select **Rahul**, open My Activity, and approve the request.
4. Select **Amritanshu**, open My Activity, and show:

   > Request approved — Accepted
   >
   > Rahul has approved your request for his Cricket Bat.
   >
   > Please contact the owner to arrange the handover.
   >
   > Owner: Rahul
   >
   > Demo contact: rahul@example.com
   >
   > Expected return: the date chosen in step 2.

5. Select Rahul and mark the bat returned before repeating the demo.

## Show competing requests

1. With Rahul's Cricket Bat available, request it as **Amritanshu**.
2. Switch to **Priya** and request the same bat.
3. Switch to **Rahul**. Both requests are Pending in My Activity.
4. Approve Amritanshu's request. Priya's request is automatically Rejected.
5. Switch to Priya to show the rejected request, then Amritanshu to show the approval/contact card.
6. The bat is absent from Explore. Switch to Rahul to record its return.

## Show rejection and validation

- Request an available Rahul-owned item as Priya; switch to Rahul and reject it. The item stays available.
- An owner sees “Your item,” rather than a borrow button, on their own listings.
- Required listing fields and the date picker guide input. Backend validation also rejects invalid dates, self-borrowing, non-owner decisions, duplicate Pending requests, and stale actions.
- Refresh after changes to demonstrate saved state. The app does not automatically reset or re-create seed items on restart.

## Focused automated check

macOS / Linux:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Windows PowerShell or Command Prompt:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

These checks use temporary databases and leave the visible demo untouched. They cover the complete lifecycle/contact card/restart, competing approvals/database uniqueness, and validation/owner/CSRF checks. No broad test suite is required for the demo.
