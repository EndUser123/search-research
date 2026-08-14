---
title: "in microsoft outlook, how do I change my gmail password?"
date: "2026-07-28"
mode: "COPILOT"
uuid: "1bba3f32-9910-4775-946f-45d2af8f3277"
entry_count: 6
---

## Human

in microsoft outlook, how do I change my gmail password?

## Assistant

You can’t change your Gmail password inside Outlook itself; you change it with Google first, then Outlook updates its saved sign-in when you reconnect. Microsoft’s guidance says to change the password with the email provider, and then Outlook will prompt for the updated password the next time it connects.[1]

## What to do
1. Open your Gmail/Google Account in a browser.
2. Change your password there.
3. Open Outlook again and sign in when prompted with the new password.[1]

## If Outlook still keeps asking
If Outlook doesn’t automatically prompt or keeps failing, remove the Gmail account from Outlook and add it back so it can re-authenticate with Google’s sign-in flow. For Gmail accounts using two-factor authentication, Google may require an app password or OAuth re-sign-in instead of a manually edited password in Outlook.[2]

## The key point
Outlook stores the connection details, but Gmail controls the actual password. So the password change happens on Google’s side, not in Outlook.[2][1]

Would you like the exact steps for classic Outlook, the new Outlook, or Outlook on Windows 11?

## Human

PS P:\> npx -y @codefuturist/email-mcp setup
┌  email-mcp › Add Account
│
◇  Account name
│  [brsthomson@hotmail.com](mailto:brsthomson@hotmail.com)
│
◇  Email address
│  [brsthomson@hotmail.com](mailto:brsthomson@hotmail.com)
│
◇  Full name (optional)
│
│
◆  Auto-detected: Outlook / Hotmail
│
●    IMAP: outlook.office365.com:993 (TLS)
│
●    SMTP: smtp.office365.com:587 (STARTTLS)
│
◇  Use detected settings?
│  Yes
│
◇  Username
│  [brsthomson@hotmail.com](mailto:brsthomson@hotmail.com)
│
◇  Password / App Password
│  ▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪
│
◇  IMAP ✗ Command failed
│
◇  SMTP ✗ Invalid login: 535 5.7.139 Authentication unsuccessful, basic authentication is disabled. [MW4PR03CA0296.namprd03.prod.outlook.com 2026-07-28T19:06:54.596Z 08DEECDB4418F57E]

## Assistant

That error means the account is trying to use legacy SMTP login, but Microsoft is rejecting it because basic authentication is disabled for the mailbox or tenant. In practice, the fix is usually to use OAuth/modern auth for the connection, or, for a Microsoft 365 business mailbox, have an admin enable Authenticated SMTP for that mailbox if your app truly requires SMTP AUTH.[1][2][3]

## What this means for your case
Your account looks like a Hotmail/Outlook personal mailbox, so the important distinction is that Outlook.com personal mailboxes do not support basic SMTP auth, even with app passwords; they require modern authentication. If `email-mcp` only supports username/password SMTP and IMAP, it will fail against this account unless it supports OAuth2.[3][4]

## What to do next
1. Check whether `email-mcp` supports Microsoft OAuth2/modern auth for Outlook/Hotmail accounts. If it does, use that flow instead of raw username/password.[4][3]
2. If it does not support OAuth2, use a different provider or a mailbox type that supports the authentication method the tool needs.[4]
3. If this is actually a Microsoft 365 business mailbox under an org tenant, ask the admin to enable Authenticated SMTP for that mailbox in Microsoft 365 admin settings.[2]

## Why the app password didn’t work
App passwords are tied to older basic-auth style flows, and Microsoft’s current guidance says basic auth is disabled in Exchange Online, while Outlook.com personal mailboxes require modern auth for SMTP. So even though an app password may exist in some Microsoft account contexts, it won’t solve a client that is still authenticating through legacy SMTP login.[5][1][4]

## Fastest resolution path
The fastest path is to confirm whether `email-mcp` can do OAuth2; if not, treat this as a tooling limitation rather than a password problem. If you want, I can help you check the exact `email-mcp` auth options and map the next step for your setup.[3][4]

## Human

are there cli tools instead of mcp that allows all the email access for gmail and outlook?

## Assistant

Yes — there are CLI tools, but the best choice depends on whether you want a **terminal email client** or a **programmable API/CLI** for automation. For Gmail, the cleanest path is usually Gmail API–based tooling; for Outlook/Hotmail/Microsoft 365, you generally want tools that support OAuth2 or Microsoft Graph rather than plain username/password SMTP/IMAP.[1][2][3]

## Good CLI-style options
- **aerc**: terminal email client that can work with IMAP/SMTP and is commonly used for serious CLI email workflows.[4][1]
- **NeoMutt / Mutt**: classic terminal mail clients; they’re flexible, but for Gmail/Outlook you still need modern auth or a compatible bridge because legacy basic auth is increasingly blocked.[5][3]
- **Himalaya**: CLI email client designed for modern providers and developer workflows, including OAuth-friendly setups.[1]
- **Nylas CLI**: more of a developer email API/CLI layer than a traditional mail client; useful if you want programmatic send/read/search operations.[1]
- **swaks / mailx / msmtp**: useful for sending and testing SMTP, but they are not full “all email access” solutions by themselves.[1]

## What works best for Gmail
For Gmail, CLI tools that use the **Gmail API** or OAuth are the most reliable because Google has tightened access around older auth methods. A terminal client can work well, but it needs to authenticate in a modern way rather than relying on a simple password login.[6][5]

## What works best for Outlook
For Outlook/Hotmail, the key issue is authentication: Microsoft has disabled basic auth in Exchange Online and personal Outlook/Hotmail flows also rely on modern authentication. So if you want “all email access,” pick a CLI/tool that explicitly supports OAuth2 or Microsoft Graph, not just IMAP/SMTP with a password.[2][3][7][1]

## Practical recommendation
If your goal is **interactive terminal email**, start with **aerc** or **Himalaya**. If your goal is **automation and scripting**, use provider APIs directly: Gmail API for Gmail, Microsoft Graph for Outlook, or a wrapper CLI that sits on top of those APIs.[4][2][1]

## Important caveat
There is no single old-school CLI that will reliably give “all email access” to both Gmail and Outlook using only username/password, because both ecosystems now push modern auth and frequently reject basic authentication. The deciding factor is not the CLI shell itself; it’s whether the tool supports OAuth2 or provider APIs.[3][7][2][1]

Would you like a shortlist specifically for **Windows 11 / PowerShell**, or a setup recommendation for **Gmail + Outlook together**?

## Human

it's for a 'todo' skill, so it can check my email for me and do things if I want from claude code, codex, and grok build, and opencode and pi.

## Assistant

Yes — but for your use case, I would not center the design around a generic mail CLI. For a “todo” skill that needs to **read, summarize, search, draft, send, label/move, and maybe trigger follow-up actions** from Claude Code, Codex, Grok Build, OpenCode, and Pi, the most robust architecture is provider APIs with OAuth, not traditional IMAP/SMTP terminal tools.[1][2][3]

## Best fit
For **Gmail**, use the Gmail API or Gmail OAuth-capable tooling, because Google officially supports OAuth2 for IMAP/POP/SMTP and API-based access is cleaner for automation workflows. For **Outlook/Hotmail/Microsoft 365**, use Microsoft Graph for mail operations such as sending and message access, because Microsoft’s modern path is Graph/OAuth rather than basic-auth SMTP logins.[4][5][2][3][1]

## Why not plain CLI mail clients
Tools like **Himalaya** are closer to what you want than old-school clients because they support Gmail and Outlook with OAuth2 rather than just passwords. But they are still fundamentally user-facing mail clients, and browser-based OAuth plus token storage can be awkward in headless or multi-agent automation scenarios, especially when several AI tools need consistent delegated access and action control.[6][7][8]

## Better architecture
The strongest design is a small local **email action service** that exposes your own normalized commands such as `list_threads`, `get_message`, `search_mail`, `draft_reply`, `send_reply`, `archive`, `label`, and `create_todo_from_mail`, while internally routing Gmail accounts to Gmail API and Microsoft accounts to Graph. That gives every agent the same stable interface, avoids provider-specific auth quirks in each tool, and lets you enforce permissions, audit logs, confirmation rules, and “read-only vs action” modes in one place.[5][2][3][4][1]

## Practical options
| Option | Gmail | Outlook | Good for your “todo” skill? |
|---|---|---|---|
| Traditional IMAP/SMTP CLI | Possible with OAuth2, but awkward for automation [1] | Often painful because basic auth is deprecated and modern auth is required [9][3] | Weak |
| Himalaya CLI | Supports Gmail and Outlook with OAuth2 [6][8] | Supports Outlook OAuth2 paths [6] | Decent for interactive use, limited as shared automation backend |
| Nylas-style unified CLI/API | Designed for terminal and unified provider workflows [10][4] | Same unified model [10] | Better, but adds third-party dependency |
| Direct provider APIs | Native and well-supported [4][1] | Native and well-supported [2][5] | **Best** |

## Recommendation
For your setup, I’d build a **local Node or Python email skill service** instead of hunting for one CLI that magically does everything. The right target is: OAuth once per account, store refresh tokens securely, normalize Gmail + Outlook into one tool contract, and let Claude Code/Codex/Grok Build/OpenCode/Pi call that contract with guardrails for destructive actions.[2][3][1]

FACT: provider APIs are the most future-proof path here. CONSENSUS: generic password-based mail tooling is becoming less reliable across major providers. SPECULATION, high confidence: if you build on IMAP/SMTP-first tooling now, you will spend more time on auth edge cases than on the actual todo workflow.[3][9][1][2]

Concrete next step:
1. Start with Gmail API + Microsoft Graph only.
2. Expose a single local CLI or HTTP service.
3. Make actions confirmation-gated for `send`, `delete`, `move`, and `archive`.
4. Add read-only commands first: inbox scan, priority detection, summarize, extract tasks.

Would you like a minimal TypeScript design for that local email skill service, with command schema and OAuth/token layout?

## Human

but with a service don't I need to run it all the time?

## Assistant

You don’t have to run a long‑lived daemon; you can treat the “service” as a **stateless command** that spins up only when a tool/agent needs email access and then exits. The always‑running piece can be optional, not required.

## Two patterns that fit your workflow

### 1. On‑demand “service” (no daemon)
Think of it as a **CLI skill binary** rather than a background process:

- You define a single command, e.g. `email-skill`, that:
  - Reads a JSON request from stdin (e.g. “list inbox tasks for account X”).
  - Uses stored OAuth tokens for Gmail/Outlook (securely on disk).
  - Calls Gmail API or Graph once, performs the action, writes JSON to stdout, and exits.[1][2][3]
- Claude Code, Codex, Grok Build, etc. invoke that command as a tool when they need email, just like MCP tools, but the process only lives for that one call.[4]

You get:
- No always‑on service.
- Deterministic behavior (each call is fresh against the providers).[2][3]
- Multi‑terminal isolation: each terminal/worktree still uses the same single command as the interface.

### 2. Optional daemon for heavy tasks
If you later want background scanning (e.g. “watch inbox for new tasks”), you can layer a **daemon process** that is started only when needed:

- A PowerShell or Node launcher ensures at most one instance via a named mutex or lock file (we already explored this pattern for your “dreaming with daemons” design).[5]
- Your agents still talk to it via CLI or HTTP, but you choose when it is running (per session or per project), not “always on”.

This becomes an optimization, not a requirement.

## Why API + stateless CLI is cleaner than pure MCP here
- Gmail and Outlook both expect OAuth/modern auth, not long‑term basic‑auth SMTP/IMAP, so any robust solution will be storing refresh tokens and calling APIs anyway.[3][4][6]
- Wrapping that into a **single CLI tool** lets your orchestrator (Claude Code/Grok Build) use one interface, while you avoid extra infrastructure or services.[1][2]

FACT (APIs): Gmail and Outlook provide stable mail APIs and OAuth flows designed for this pattern.[1][2][3]
CONSENSUS: Always‑running basic‑auth daemons are increasingly brittle on modern providers.[4][6]
SPECULATION (high confidence): A stateless email CLI per call will match your multi‑terminal, deterministic preferences better than an MCP‑first design with background services.

Concrete next step:
- Define an `email-skill` CLI contract (JSON in/out) and wire it as a tool for Claude Code/Codex/Grok Build/OpenCode/Pi. Behind that, implement Gmail + Graph calls with stored OAuth tokens, no daemon.

Would you like me to sketch that CLI contract and a minimal Node/TypeScript skeleton that you can drop into your PowerShell‑first workflow?

## Human

are there repos for this already?

## Assistant

There are repos and tools that get **close**, but none that perfectly match “local, stateless CLI, unified Gmail + Outlook, designed for AI agents” out of the box. The closest patterns are modern email CLIs and unified API CLIs, plus some libraries you could wrap into your own skill.[1][2][3]

## Existing tools that are very close

### Himalaya (Rust, CLI mail client)
- **What it is**: A terminal email client that outputs JSON and supports IMAP/SMTP, OAuth2, and scripting.[4][5][1]
- **Providers**: Gmail and Outlook are supported via OAuth2 with IMAP/SMTP; you configure OAuth apps in Google Cloud and Azure, then Himalaya uses browser-based OAuth and stores tokens in OS keyring.[6][7]
- **Pros**:
  - Already CLI-first and script-friendly (JSON output).
  - Handles modern auth for Gmail + Outlook, with documented setup guides.[1][6]
- **Cons relative to your “todo skill”**:
  - Its OAuth flow assumes **interactive browser redirect**, which is fragile for true agent use or fully headless flows.[7][6]
  - Interface is a general mail client, not a normalized “email-todo” command set tailored to agents.

### Nylas CLI (unified provider API client)
- **What it is**: Open-source CLI that talks to Gmail, Microsoft 365/Outlook, Exchange, Yahoo, iCloud, and IMAP via the Nylas platform, exposing unified commands for email, calendar, contacts.[8][2][3]
- **Pros**:
  - Single CLI that handles multi-provider OAuth, token storage, and unified commands.[2][3]
  - Has Node guides showing how to call it from scripts; it effectively acts as the auth and API abstraction layer.[9]
- **Cons for your constraints**:
  - Depends on Nylas’ cloud API rather than directly on Gmail/Microsoft Graph; adds another vendor and remote dependency.[3][8]
  - Not designed specifically as an “agent skill” contract, though you could treat it that way.

## Libraries / patterns you could wrap

If you’re willing to write a thin skill around existing libraries:

- **Gmail OAuth2 + SMTP/IMAP**: Multiple guides and repos show Gmail OAuth2 for IMAP/SMTP, commonly using MailKit (.NET), or Google’s official client libraries and Nodemailer for Node.[10][11][12][13]
- **Gmail API**: Gmail API docs and example repos provide Node, Python, and .NET clients; you can expose your own CLI around that.[13][14]
- **Microsoft Graph mail**: Graph has REST APIs for send/read/move, and example repos show how to call `sendMail`, list messages, etc., using OAuth app registrations.[15][16][17]

These are **not** full “email-todo skill” repos, but they are solid building blocks for a small CLI that you control.

## Answering your underlying question

FACT: There are open-source CLIs that already support **Gmail + Outlook with OAuth** (Himalaya, Nylas CLI) and can be scripted from other tools.[6][2][3][1]
CONSENSUS: Those CLIs are aimed at human terminal use, not AI agents; their OAuth flows and UX aren’t tailored to multi-agent orchestration like Claude Code + Grok Build.[8][7][6]
SPECULATION (high confidence): Adapting one of these CLIs as a backend and wrapping it with a thin “email-todo skill” CLI of your own will be faster than building everything from scratch, but you’ll likely still need custom glue to normalize commands, results, and confirmation rules.

Concrete next step:
- Pick either **Himalaya** (direct email protocols) or **Nylas CLI** (unified API) as the low-level email engine.
- Then design a small Node/Python CLI that:
  - Accepts a JSON command (e.g. `list_tasks_from_inbox`).
  - Calls the underlying CLI/library.
  - Returns normalized JSON focused on “todo” items for agents.

Do you lean more toward **using Nylas CLI as a unified backend** or **building directly on Gmail API + Microsoft Graph with your own minimal CLI?**
