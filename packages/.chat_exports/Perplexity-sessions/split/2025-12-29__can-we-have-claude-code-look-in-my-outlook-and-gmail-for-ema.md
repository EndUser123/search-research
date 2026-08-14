---
title: "Can we have Claude code look in my outlook and gmail for emails from me to me automatically and ask me what to do with t"
date: "2025-12-29"
mode: "CONCISE"
uuid: "db85f92c-31c0-4a8e-a8fa-119fd09a6a50"
entry_count: 2
---

## Human

Can we have Claude code look in my outlook and gmail for emails from me to me automatically and ask me what to do with them?   Some are for research and some are reminders.

## Assistant

Yes, you can absolutely have a Claude Code-style agent watch both Outlook and Gmail for “from me to me” messages, classify them (research vs reminder), and then ask what to do with each.[1][2]

Below is a high‑level architecture tailored to your stack, plus concrete implementation steps.

## Overall architecture

You’d build a small **local orchestrator** service that:

- Connects to:
  - Gmail via Gmail API with OAuth and `Mail.readonly`/`Mail.readwrite` scopes.[3][1]
  - Outlook (Microsoft 365) via Microsoft Graph `Mail.ReadWrite` for your account.[2][4]
- Polls both accounts for:
  - `from:me to:me` (Gmail search query) and `from eq me and toRecipients any` (Graph filter).[5][6][4]
- For each new self‑email:
  - Extracts subject, body snippet, and headers.
  - Sends a structured prompt to Claude Code (“Is this research, reminder, or other? What action do you suggest?”).
  - Surfaces the suggestion to you in your preferred channel (CLI prompt, small local web UI, or even a “daily digest” email).
- Applies actions you confirm:
  - Add labels / move to folder (e.g., `Research`, `Reminder`, `Archive`).[3][5]
  - Optionally create calendar tasks/events for reminders via Microsoft Graph / Google Calendar.

## Gmail side

**1. Auth & setup**

- Use the official Python quickstart to set up OAuth and get a token for your Google account.[7][1]
- Request scopes:
  - `https://www.googleapis.com/auth/gmail.readonly` (start here)
  - Later, `.../gmail.modify` to add labels / archive.[3]

**2. Query “me → me” emails**

- Use the Gmail API `users.messages.list` with a query like:[6][5]
  - `from:me to:me -in:trash -in:spam`
- Store last processed message ID or history ID so you only handle new items.

**3. Actions**

- Use `users.messages.modify` to:
  - Add label `Research` or `Reminder` (create if needed).
  - Remove `INBOX` to archive when appropriate.[8][3]

## Outlook / Microsoft 365 side

**1. Auth & setup**

- Use Microsoft Graph with an app registration (single-tenant, delegated permissions).[4][2]
- Scopes:
  - `Mail.Read` or `Mail.ReadWrite` for your mailbox.[2]

**2. Query “me → me”**

- Use `GET /me/mailFolders/SentItems/messages` or `/me/messages` with a `$filter` such as:[9][4]
  - `from/emailAddress/address eq '{your_email}' and toRecipients/any(t:t/emailAddress/address eq '{your_email}')`
- Or just pull recent messages and filter client-side on from/to equality.

**3. Actions**

- Use Graph to:
  - Move messages to folders like `Research` or `Reminders`: `POST /me/messages/{id}/move`.[4]
  - Add categories (color tags) as lightweight labels.[2]

## Claude Code “what to do with this?” loop

You can wrap this in a simple decision loop:

1. Poll both providers every N minutes (or use push webhooks later).
2. For each unclassified self-email, construct a JSON payload:

   - `subject`
   - `snippet` (first N chars of body)
   - `full_body` (optional for long research notes)
   - `source` (`gmail`/`outlook`)
   - `message_id`

3. Send that into Claude with a system prompt like:

   > You are my personal triage agent. Classify each email I send to myself as `"research"`, `"reminder"`, or `"other"`. Suggest one concrete action from: `["label_research", "label_reminder", "archive", "create_calendar_event"]`. Respond in strict JSON.

4. Present Claude’s suggestion to you:
   - Easiest: CLI interactive prompt in your local script.
   - Or a tiny web UI listing pending items with buttons.
   - Or a “morning digest” email summarizing all suggestions.

5. On confirmation, call the appropriate Gmail/Graph API methods to apply labels/folders or create calendar items.

## Minimal concrete implementation plan (Python)

**Phase 1 – Prototype loop (read-only):**

- Implement `gmail_client.py` using the Google Python quickstart; add a function `get_self_emails_since(token)` with query `from:me to:me`.[1][5]
- Implement `outlook_client.py` using the MS Graph Python tutorial; add `get_self_emails_since(token)`.[9][2]
- Implement `triage_agent.py` that calls Claude with a list of new emails and prints a proposed classification and action per email to the console.

**Phase 2 – Semi-automatic:**

- Add a small state store (SQLite or JSON file) keyed by message ID with `status = pending|done`.
- For each pending item:
  - Ask you in CLI: “Gmail: [subject] – classify as Research / Reminder / Ignore?”.
  - On selection, apply label/folder changes via Gmail/Graph modify calls.[3][2]

**Phase 3 – More automation:**

- Allow a “trust mode” where if Claude’s confidence is high and the pattern is familiar (e.g., subject starts with “TODO:”), it auto-applies the action and logs it for review.

***

If you want, next step can be a concrete repo layout plus example Python functions for:

- `fetch_self_emails_gmail()`
- `fetch_self_emails_outlook()`
- `triage_with_claude(messages)`
- `apply_actions(actions)`

## Human

Can it then move those emails into an “actioned” folder?

## Assistant

Yes, the system can move actioned emails to an "Actioned" folder after you confirm Claude's classification and suggested action.[1][2][3]

Gmail uses labels instead of traditional folders, so create an "Actioned" label and apply it while removing "INBOX" to simulate moving.  Outlook supports true folder moves via Microsoft Graph.[2][4][3][5][1]

## Gmail Implementation

Use the `users.messages.modify` API endpoint to add the "Actioned" label ID and remove "INBOX".[5][2]

**Key steps:**
- Create label via Gmail UI or API: `users.labels.create` with `{"name": "Actioned", "labelListVisibility": "labelShow", "messageListVisibility": "show"}`.[1]
- Get label ID from `users.labels.list()`.
- For actioned message: `POST /gmail/v1/users/me/messages/{msgId}/modify`
  ```json
  {
    "addLabelIds": ["Actioned_label_id"],
    "removeLabelIds": ["INBOX"]
  }
  ```
- Python example using `google-api-python-client`:
  ```python
  service.users().messages().modify(
      userId='me', id=msg_id,
      body={'addLabelIds': [actioned_label_id], 'removeLabelIds': ['INBOX']}
  ).execute()
  ```

## Outlook Implementation

Use `POST /me/messages/{id}/move` with `{"destinationId": "Actioned_folder_id"}`—this creates a copy in the target and deletes the original.[4][3]

**Key steps:**
- Create folder: `POST /me/mailFolders` with `{"displayName": "Actioned", "parentFolderId": "inbox_id"}`.[6]
- Get folder ID from `GET /me/mailFolders`.
- Move: 
  ```python
  # Using msgraph-sdk
  request_body = MovePostRequestBody(destination_id="Actioned_folder_id")
  result = await graph_client.me.messages.by_message_id(msg_id).move.post(request_body)
  ```
- Well-known folders like "inbox" also work by name.[3]

## Integration in Triage Loop

Extend the Claude response handling:

1. After you approve "label_research" → applies Research label + optionally moves to Actioned.
2. Add `"move_to_actioned"` as a Claude-suggested action.
3. Track in SQLite: `status=actioned, actioned_at=timestamp, folder_id=...`.
4. Run daily cleanup: Move any stale "pending" → "Actioned".

This keeps your inbox clean while preserving audit trail.[7]
