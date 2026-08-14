---
title: "NotebookLM is not letting me delete notebooks.  any idea on how to make it delete?"
date: "2026-04-22"
mode: "CONCISE"
uuid: "50c9bd3e-0e27-469e-acd3-cc5c550c056d"
entry_count: 5
---

## Human

NotebookLM is not letting me delete notebooks.  any idea on how to make it delete?

## Assistant

Based on the search results, the standard process to delete a notebook in NotebookLM is:[1][2]

1. **Click the three-dot menu** (sometimes called a "snowman menu") next to the notebook you want to delete[3][1]
2. **Select "Delete notebook"** from the dropdown[2][1]
3. **Confirm the deletion** when prompted[4][5]

## If the Delete Option Isn't Appearing

If the delete button is missing or not working, here are the most likely culprits:

- **UI bug or language/translation issue** — There's a known Reddit report  of the edit/delete options disappearing in certain language translations, where menu button text becomes too wide. Try switching your NotebookLM language setting to English (US) and refresh.[6]
- **Browser cache** — Clear your browser cache and cookies, then try again[7]
- **Insufficient permissions** — If the notebook is shared with you but you don't own it, you may not have delete rights
- **Notebook at capacity limits** — Though less common, check if you've hit the notebook limit (100 on free tier, 500 on paid)[8]

## Programmatic Alternative

If the UI remains broken, you can use the **NotebookLM SDK**  to delete notebooks programmatically via TypeScript/Node, though this requires API access setup.[9]

**What exactly are you seeing when you try to delete?** Are the three dots menu appearing but the delete option is missing, or is there an error message when you click delete?

## Human

the three dots appear when I click delete the row disappears when I refresh the page the row is back.

## Assistant

That's a classic **client-side deletion UI bug** — the notebook is being marked as deleted in the frontend but the deletion isn't persisting to NotebookLM's backend.[1]

## What's Happening

When you click delete and the row disappears, NotebookLM is removing it from the local UI state optimistically (assuming the delete will succeed). When you refresh, the backend never received the deletion request, so it sends the notebook back down. This suggests either:

1. **The deletion request is failing silently** — The API call to delete is returning an error, but NotebookLM isn't showing you the error message
2. **Network timeout** — The delete request times out before completing
3. **Session/authentication issue** — Your session may have expired or permissions changed mid-request

## How to Fix It

**Immediate troubleshooting:**
- **Check browser console for errors** — Open DevTools (F12 or Cmd+Option+I), go to the Console tab, attempt deletion, and screenshot any red errors. This will tell you exactly why it's failing.
- **Check Network tab** — Go to DevTools → Network, attempt deletion, and look for a failed request (red/orange). Check the response to see what error the backend returned.
- **Sign out and back in** — Your session may be stale. Completely sign out of NotebookLM, close the browser tab, and sign back in.
- **Try a different browser** — Rules out browser-specific issues (cache, extensions, etc.)
- **Wait 24 hours, then try** — If there's a backend sync issue, NotebookLM may need time to reconcile state.

**If those don't work:**
- Contact Google NotebookLM Support  with a screenshot of the DevTools Console errors and the notebook name/ID. They can check server-side logs to see if the deletion request even arrived.[2]

The console/network inspection will tell you whether this is a client-side UI bug, an API failure, or a permissions issue. What do the DevTools errors show?

## Human

Can you check to see if there are any notebook LM infrastructure issues from Google?

## Assistant

Short answer: there’s no *major, ongoing* NotebookLM outage reported right now, but there are signs of **localized / intermittent issues** affecting some users, and your “delete doesn’t stick” behavior is consistent with that.

### 1. Official + third‑party status

- **Google Workspace Status Dashboard** lists NotebookLM as *Available* as of today (Apr 22, 2026). There’s no current, active incident banner for NotebookLM right now.[1]
- The **incident history** shows past problems with NotebookLM access, but nothing currently open that matches “can’t delete notebooks.”[2]
- Third‑party monitors (StatusGator, etc.) show **NotebookLM “up”**, but also note user‑reported issues in the last 24 hours.[3]
- Another checker reports **“All Systems Operational”** for NotebookLM with no incidents in the last 7 days.[4]

So: core service is generally up; Google isn’t flagging a global incident. But status pages are notoriously coarse‑grained, and silent bugs in specific flows (like delete) often don’t get their own entry.

### 2. Evidence of quality / regression issues

- Recent Reddit threads (early April 2026) complain about NotebookLM reliability and regressions in core features. That’s not proof of a delete‑API bug, but it supports the idea that rough edges are present and not always reflected on the status page.[5]

Given your symptom:

> click delete → row disappears → refresh → row returns

that’s classic **optimistic UI update with a failed backend write**. Either:

- the delete API call is failing (4xx/5xx), or  
- some internal consistency check rejects the delete, or  
- a replication lag / caching layer is restoring the notebook from stale state.

All of those can happen even while the high‑level status page stays green.

### 3. What I’d do next (minimal time / maximum signal)

Because there’s no confirmed global incident, I’d treat this as a **likely partial/buggy behavior** and gather enough evidence that if you go to support, you’ll get past tier‑1 quickly.

1. **Try a different browser & account check (5 minutes)**
   - Log into NotebookLM in a different browser (e.g., Edge/Firefox if you’re on Chrome) and try deleting the *same* notebook.  
   - If you have a secondary Google account, create a test notebook there and see if delete works in that account.  
   - Outcome:
     - Works elsewhere → likely account‑specific or browser‑state issue.
     - Fails consistently across accounts/browsers → points toward a backend bug or policy constraint rather than local cache.

2. **Quick admin check (if you’re on a Workspace domain)**
   - If this is under Google Workspace, an admin could have NotebookLM toggled or in a weird state; the admin console can turn NotebookLM on/off per OU.[6]
   - Ask/verify: NotebookLM is enabled and not in some partially‑restricted configuration.

3. **DevTools, but targeted**
   - Open DevTools → Network tab.  
   - Filter by `notebook` or `delete`.  
   - Click delete on a notebook.  
   - Look for a request that fails (red) or returns non‑2xx; pop open the Response and Status code.  
   - This will tell you if it’s:
     - **401/403** → auth/permissions problem  
     - **400/404** → logic / data issue  
     - **5xx** → NotebookLM backend error  
   - That one screenshot is gold when filing a bug or talking to support.

4. **Escalate with evidence**
   - Use official NotebookLM / Google Workspace support channels and include:
     - Time window  
     - Region (Calgary, Canada)  
     - Browser(s) tried  
     - Status code + snippet from the failing delete request  
   - Since status is “Available,” this is probably not on their radar yet; having HTTP status + response body tends to move it faster than “it doesn’t delete.”

### 4. Practical workarounds meanwhile

These are ugly, but in case you’re blocked:

- **Rename + archive pattern:**  
  Prefix with something like `_TRASH_` and move those notebooks to an “Archive” or “Trash” naming convention so they’re out of your main working set. (You’ve probably already considered this.)

- **Check if there’s a per‑user limit interaction:**  
  There are hints about deletion questions and bulk limits from users discussing hitting many notebooks. If you’re operating at large scale, it’s plausible some unpublicized constraint is glitching deletes under high count.[7]

***

**Summary:** Officially, NotebookLM is “up” with no active outage today, but your behavior is consistent with a **non‑surfaced backend bug or partial failure in the delete path** rather than just a UI quirk. I’d very quickly test in another browser/account, grab one failing delete request from DevTools, and then file it with support; absent that, status dashboards won’t help much.[3][1][4]

Do you want help walking through exactly what to click in DevTools to capture the failing delete request and reduce it to something you can paste into a support ticket?  

## Human

In firefox, I can't delete any of my notebooks.

## Assistant

Given that:

- Delete appears to work in the UI but **never persists**, and  
- You see the same behavior in Firefox (i.e., across browsers),

this strongly suggests it’s **not** just a browser quirk; it’s either:

- an account‑/workspace‑level issue, or  
- a current NotebookLM bug in the delete path that isn’t on the public status page.

I don’t see any public, documented “can’t delete notebooks” incident specific to Firefox or to April 2026. Status dashboards still show NotebookLM as operational. So we’re in “real bug, not yet acknowledged” territory.[1][2][3][4]

Given your stack‑y mindset, here’s how I’d proceed, ordered by signal‑to‑effort:

***

## 1. Rule out policy / limits

NotebookLM has documented limits: around **100 notebooks** and per‑notebook source caps on the free tier in 2026. There’s no official statement that hitting limits blocks deletes, but if you’re at or near those numbers, that raises the odds of weird edge cases.[5]

**Quick checks:**

- Roughly how many notebooks do you have?  
- Are you on:
  - personal Google account, or  
  - Workspace (where an admin might have toggled / partially disabled NotebookLM)?[6]

If it’s Workspace, have the admin quickly toggle NotebookLM off → on for your OU in the admin console and retry delete.[6]

***

## 2. Confirm that *no* notebooks delete in Firefox

You said “I can’t delete any of my notebooks” — that’s already strong evidence, but just to be precise:

- Create a **brand‑new test notebook** in Firefox.  
- Immediately try to delete it via the 3‑dot menu.  
- If that also comes back after refresh, that’s a clean repro with:
  - minimal data
  - no legacy content
  - same failure mode

That’s a perfect repro case for support.

***

## 3. Capture one failing delete in DevTools (Firefox‑specific steps)

This is the highest‑value thing you can do right now; it turns “it doesn’t work” into actionable data.

1. Open NotebookLM in Firefox and sign in.  
2. Press **F12** (or Menu → More Tools → Web Developer Tools).  
3. Switch to the **Network** tab.  
4. In the filter box, type `delete` or `notebook` to narrow down, but keep “All” selected if possible.  
5. Now click the **three dots → Delete** on one notebook.  
6. Watch the Network panel:
   - Look for a request that fires at click time; likely `DELETE ...`, `PATCH ...`, or a `graphql`/`batch` call.
   - Any entry that turns red or shows **status 4xx or 5xx** is what we care about.
7. Click that failing request and check:
   - **Status code** (e.g. 400 / 401 / 403 / 404 / 500 / 503)  
   - **Response body** (often JSON with an error message or internal code)  

Copy out:

- Request URL (you can redact IDs if you like)  
- Status code  
- Response body (or at least the `error` / `message` field)  

That’s the difference between “it feels broken” and “your delete calls are getting 403 due to X.”

***

## 4. Fast local eliminations in Firefox

While you have DevTools open, it’s cheap to eliminate local interference:

1. **Private window test**
   - Open a **Private Window** in Firefox.  
   - Log into NotebookLM.  
   - Try deleting the test notebook again.  
   - If it works here but not in your normal session, your main profile’s cookies/local storage/extension set is suspect.

2. **Disable extensions**
   - Temporarily disable:
     - ad blockers  
     - script blockers  
     - any NotebookLM‑related or “research helper” extensions (e.g., NotebookLM Tools, ExtendLM, etc.).[7][1]
   - Reload NotebookLM and retry delete.  
   - If it starts working, re‑enable extensions one by one to find the culprit.

This is mostly to be thorough; your “works nowhere and reappears on refresh” pattern still smells more like a server‑side failure, but we can eliminate extension‑injected JS as a confounder.

***

## 5. Escalate with a minimal, precise repro

Once you have the Network details from one failed delete:

- Go to **NotebookLM Help / contact support**.[2][8]
- Provide:

  - “In Firefox (version X) on <OS>, I cannot delete any NotebookLM notebooks.”  
  - Repro:
    1. Sign in to NotebookLM.  
    2. Create a new notebook.  
    3. Click three dots → Delete → confirm.  
    4. Notebook disappears, but after page refresh, it returns.  
  - The **HTTP request** from DevTools:
    - URL (redacted IDs ok)  
    - Method (likely DELETE or POST)  
    - Status (e.g., 403)  
    - Response snippet (e.g., `{"error":"PERMISSION_DENIED","message":"..."}"`)

That’s the kind of report that usually bypasses the generic “clear cache and cookies” script and gets straight to engineering.

***

## 6. Interim workaround that keeps you moving

Until Google fixes it:

- Use a simple convention like `__Z_TRASH_YYYYMMDD__` prefix on notebook names so you can filter them out mentally.  
- If you use NotebookLM browser extensions that support **bulk deletion or cleaning**, be cautious: if the underlying API delete is failing, those may also “seem to delete” but not persist.[1][7]

***

If you’re up for it, the next step that’s most useful is:

**Can you grab the status code + response from one failed delete request in Firefox’s Network tab and paste it here (with IDs redacted)?**

I can help you interpret exactly what the backend is complaining about and draft a tight support report for you.  

## Human

personal pro plan.

## Assistant

Got it: personal Google account on the **Pro plan** (Google AI Pro / NotebookLM Pro). That rules out most Workspace-admin policy weirdness and also means you’re well within the designed use case for having lots of notebooks.[1][2][3]

Given everything so far:

- Personal Pro account → no domain admin toggles in the way.[3]
- Same delete‑doesn’t‑stick behavior in **multiple browsers**.  
- No public incident flag for NotebookLM right now.[4][5]
- Pro plan increases limits (up to ~500 notebooks and hundreds of sources per notebook), but there’s no documented behavior where hitting limits would silently prevent deletes.[6][7][2][8]

That combination makes it **very likely you’ve hit a real backend bug in the delete path for certain accounts**, not a config or plan/limit issue.

At this point, the only high‑signal next step is:

1. **Capture one failing delete call in DevTools** (status code and response body), as outlined earlier, ideally on:
   - a brand‑new test notebook,  
   - in a browser with extensions disabled / private mode.

2. Then file a report via NotebookLM Help / Google support with:
   - Your plan: “Personal account, Google AI Pro / NotebookLM Pro.”[1][3]
   - Repro steps for a brand‑new notebook.  
   - The HTTP status + response from that failing delete call.

If you paste the status code and response text from one of those delete requests here (with any IDs redacted), I’ll help you interpret it and turn it into a concise support ticket you can send to Google.

What do you see for the delete request in the Network tab — **status code and any error message**?
