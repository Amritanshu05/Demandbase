# Demo and judging walkthrough

## Before presenting

1. Follow [SETUP.md](../SETUP.md).
2. Use `http://127.0.0.1:5000` consistently.
3. Keep a normal window for the owner and an incognito window for the recipient.
4. Prepare a small TXT/CSV/PDF document. No fake seed data is required.
5. Run the automated suite using [TESTING.md](TESTING.md).

## Suggested presentation

### 1. Problem and research

“We wanted the convenience of Pastebin for more than text, while making temporary access understandable. Pastebin informed the paste/unlisted/expiry flow. PrivateBin showed why access links and actual encryption are different promises. We chose a locally runnable MVP, not a cloud-dependent release.”

Show [RESEARCH.md](RESEARCH.md). State that this is desk research, not user validation.

### 2. Text/code — prove the whole flow

1. Open **New share** → **Code**.
2. Title: `Quick CSV summary`; language: Python; expiry: 1 day.
3. Paste:

   ```python
   import csv

   with open("notes.csv", newline="") as file:
       rows = list(csv.DictReader(file))
       print(f"{len(rows)} resources ready to share")
   ```

4. Create and show the preview with preserved indentation.
5. Copy the URL; open it in incognito. No signup required.
6. Copy the content and download it as text.
7. In the owner's workspace, show the resource and recipient view count.
8. Demonstrate that the incognito workspace does not list the owner's resources.

### 3. Documents and links

1. Upload a small TXT or CSV file. Show the escaped preview and complete download.
2. Upload a PDF if time permits; explain why it is download-only.
3. Share `https://example.com` as a Link.
4. Show the explicit destination and external-navigation warning.

### 4. Revocation — include the negative path

1. Revoke an active share as the owner; confirm the prompt.
2. Reload its recipient URL: it returns a closed-access page.
3. Try the same URL with `/download` appended: access is also denied.
4. The owner dashboard shows **Revoked**; there is no restore button.

### 5. Expiry — no clock changes needed

1. Create a text share with **1 minute · demo**.
2. Open it in incognito while active.
3. Continue the architecture explanation; after the minute passes, reload.
4. Show the 410 page; try `/download` too.
5. Explain that cached/saved copies cannot be recalled and open pages are not live-erased.

### 6. Persistence and validation

1. Create a one-day share, stop with Ctrl+C, restart, reload its URL.
2. Submit an unsupported/disguised file or a `javascript:` link to show server validation.
3. Optionally disable JavaScript and demonstrate basic form submission.

### 7. Design and growth

Show [DECISIONS.md](DECISIONS.md) and [SCALING.md](SCALING.md).

“SQLite and local documents make this easy to run. Signed browser ownership avoids signup but loses recovery. Every read checks lifecycle state. A real hosted version needs TLS, recoverable identity, global abuse controls, private object storage, and eventually PostgreSQL when contention or multiple instances justify it.”

## Judging evidence map

| Criterion | Evidence |
| --- | --- |
| Working demo | Live create → recipient view/download → revoke/expire |
| Research | Linked sources and resulting decisions in RESEARCH.md |
| Functionality | Acceptance criteria and automated integration tests |
| UI decisions | Dedicated create/share/manage views, responsive layout, native controls |
| Backend decisions | Lifecycle guard, owner hash, private storage, validation |
| Tradeoffs | Browser identity, PDF downloads, unlisted not encrypted, bounded dashboard |
| Scale scope | Trigger-based roadmap, not premature distributed infrastructure |
| Local run | Dedicated instruction-only SETUP.md |

## Do not claim

Production readiness, guaranteed privacy, E2E encryption, unique-user analytics, automatic physical expiry deletion, prevention of saved copies, tested load capacity, or public link accessibility from a loopback URL.
