# Campus Commons — V0.3 hackathon walkthrough

Start using [STARTUP.md](../STARTUP.md), with macOS/Linux and Windows commands. Existing databases upgrade automatically; no reset is required. For an optional clean demo, use the [reset instructions](../README.md#reset-the-demo-database), which also remove chat history. Use only non-sensitive sample messages. Identities and contacts are fictional.

## List → request → dashboard → chat → return

1. Select **Rahul**, choose **List an item**, and create “Demo Cricket Bat” with Sports / Good and a short description.
2. Open **My Dashboard**. Show the bat under **My Items**, marked **Available**, even with no requests.
3. Select **Amritanshu**. Request that bat in Explore with today or a future return date. My Dashboard shows **Awaiting approval**.
4. Select **Rahul**. The bat's card contains Amritanshu's Pending request. Approve it.
5. Show Rahul's bat as **Lent Out**, with **Amritanshu** and the return date. It disappears from Explore.
6. Select **Amritanshu**. Under **Borrowing / Actively borrowing**, show **Request approved**, **Accepted**, and **Open chat**. Expand **Demo contact details** to show `rahul@example.com` if desired.
7. Open chat and send: “Hi Rahul! Would the campus cafe work for the handover?”
8. Select **Rahul**. Switching from chat returns to My Dashboard. Open the bat's chat and reply: “Yes, let's meet there after class.”
9. Select Amritanshu, reopen chat, and show the reply. **Refresh messages** retrieves new replies. The app supports a conversation; users arrange physical exchange themselves.
10. Select **Priya**. My Dashboard shows her own items/requests. Opening the same `/borrows/<id>` returns **403**. Sending is also denied while selected as Priya.
11. Select **Rahul** and mark the bat returned from My Dashboard or chat. It becomes Available, with no current borrower on the item card.
12. Select **Amritanshu**. The record appears in **Past requests** as Returned. Open **View conversation**: messages remain, a read-only notice is shown, and there is no send box.
13. Refresh, stop/restart the server, and show the listing, Returned record, and messages persist.

The selector intentionally allows choosing another participant. The Priya check demonstrates access control against the selected identity, not authenticated privacy.

## Seeded Rahul approval example

Use Rahul's seeded **Cricket Bat** for the same flow. Amritanshu's approval card says:

> Request approved — Accepted
>
> Rahul has approved your request for his Cricket Bat.
>
> Please message the owner here to arrange the handover.

The expected return reflects the chosen date. **Open chat** is the main action; expandable contact details retain Owner: Rahul and Demo contact: rahul@example.com. If the bat is already lent, record return as Rahul before repeating.

## Competing requests and rejection

1. With Rahul's bat Available, request it as Amritanshu, then Priya.
2. Select Rahul. Both Pending requests appear beneath the same owned item.
3. Approve Amritanshu. Priya's request becomes Rejected and cannot open chat.
4. Show Amritanshu's active borrow and chat, then record return as Rahul. History remains readable. A subsequent borrow gets a separate conversation.
5. Separately reject a Pending request to show that rejection leaves an item Available.

## Focused verification

macOS / Linux:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Windows PowerShell or Command Prompt:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Six integration checks use temporary databases. They cover listing/borrow/return, competing approvals, validation/owner/CSRF rules, dashboard inventory, chat access and persistence, Returned read-only history, and upgrades preserving existing data. They do not change the visible demo database.
