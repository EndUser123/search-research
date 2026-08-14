---
title: "in microsoft word I added the claude plugin, but it's stupid and used the wrong claude account.  How do I change it?"
date: "2026-07-12"
mode: "COPILOT"
uuid: "8914a23a-46cd-46c8-8ea2-c539a4e400d4"
entry_count: 1
---

## Human

in microsoft word I added the claude plugin, but it's stupid and used the wrong claude account.  How do I change it?

## Assistant

You change it by signing out inside the Claude sidebar in Word, then signing back in with the correct Claude account; if that fails, you remove/re-add the add‑in so it forces a fresh login.[1][2]

## How the Word add‑in handles accounts

Claude for Word uses whatever Claude account you authenticate with when the sidebar first loads; there’s no in‑Word “switch account” menu like some Microsoft add‑ins have. The account is tied to the session/token stored by the add‑in (and, for Team/Enterprise, to your organization’s deployment).[2][1]

## Steps to switch Claude accounts

Try these in order; they’re minimal changes and avoid unnecessary reinstall churn.

1. Open Word and bring up the Claude sidebar  
   - On Windows, Home → Add‑ins (or Insert → Get Add‑ins) → click “Claude by Anthropic” to open the panel.[3][1]

2. Look for a sign‑out option in the Claude panel  
   - In the right sidebar, click the menu / three‑dots / profile icon and check for “Sign out” or “Log out”.[1]
   - Confirm sign‑out, then you should be redirected to a sign‑in page.

3. Sign in with the desired Claude account  
   - Use the correct email/SSO identity (e.g., personal vs work, or the right org) when the sign‑in page appears.[2][1]
   - Once authenticated, the add‑in will now use that account for all Word interactions.[1]

If you don’t see a sign‑out button or it keeps jumping back to the wrong identity, use a harder reset:

4. Remove the Claude add‑in from Word  
   - In Word: Insert → Get Add‑ins → “My Add‑ins”, find “Claude by Anthropic”, and click Remove.[3][2]
   - Close Word completely after removing it.

5. Clear browser/SSO state for the wrong account  
   - Because the add‑in uses a web sign‑in flow, it can pick up cached login from your default browser or Microsoft 365 session.[1]
   - In your main browser, sign out from the wrong Claude account and, if applicable, from any Microsoft 365 tenant that auto‑routes you to the unwanted org.[1]

6. Re‑add Claude and sign in fresh  
   - Reopen Word → Insert/Home → Add‑ins → search “Claude by Anthropic” → Add.[3][2]
   - When the sidebar opens and prompts you, sign in with the correct Claude account (email/SSO) so the token it stores is now tied to that one.[1]

## Edge cases and constraints

- Org‑managed deployment: If your Microsoft 365 admin pushed the add‑in to your work account tenant, it may **force** sign‑in with your org’s Claude Team/Enterprise account and block personal accounts. In that case, changing accounts might require an admin to adjust the deployment or your Claude org membership.[2][1]
- Plan limitations: The Word add‑in requires a paid Claude plan (Pro/Max or Team/Enterprise) and won’t work properly if you log in with a free account, which can look like “wrong account” but is actually a plan mismatch.[4][1]
- Multiple Microsoft profiles: If you’re using different Windows or Office profiles (e.g., work vs personal), the add‑in may always associate with the profile’s corresponding tenant; switching accounts can require using Word under the profile that matches the desired Claude org.[2][1]

Most likely next step for you: open Word, sign out in the Claude sidebar if possible, then remove/re‑add the add‑in and do a fresh login with the correct email/SSO while making sure your browser isn’t auto‑logging you into the unwanted Claude account.[3][1]

To give you a more precise “do exactly this” sequence: are you trying to switch from your work Claude org to a personal Claude account, or between two work/enterprise Claude orgs?
