# 2026-08-11 - Compare conversation exports

- **Created:** 8/13/2026, 7:45:46 AM
- **Exported:** 8/13/2026, 7:45:49 AM
- **Messages:** 9
- **Source:** browser_extension

---

## #1 · user

File

File

both of these are exports of the same conversation.  Which is more useful for understanding and carrying on the work?

## #2 · user

File

Zip Archive

## #3 · user

File

This is what I'm doing to help my clis talk to you.  Is there a better way to do this, given that we are architecting and identifying features for an extension?

## #4 · user

File

## #5 · assistant

Yes. Seeing the real `model-web`, I would change the extension architecture materially.

Your current design is already fairly disciplined: the CLI remains the authority, claims a browser tab, injects an SSE capture shim, takes a pre-send snapshot, adds a nonce, submits, verifies submission, waits adaptively, extracts the fresh response, records state, and returns it to the orchestrator.  

The weakness is that **Chrome DevTools is being used as an IPC/adapter layer when an extension can sit inside the browser directly**.

## I would merge the two ideas

Don't build:

```
Extension A: conversation exporter

model-web:
CLI
 ↓
Chrome DevTools MCP
 ↓
snapshots/SSE injection/DOM
 ↓
ChatGPT
```

Build:

```
                    LOCAL WORLD
                         │
                  model-web / CLI
                         │
                  Browser Bridge
                         │
                         ▼
               EXTENSION SERVICE WORKER
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          ChatGPT      Claude     Gemini ...
          adapter      adapter     adapter
              │
              ▼
          conversation
            model
              │
       ┌──────┴────────┐
       ▼               ▼
   interaction       capture
   transport         / export
```

**The same provider adapter should power both conversation export and browser communication.**

That is the important architectural convergence.

Chrome already provides the primitives: content scripts can run persistently on matching sites, extension components can communicate over long-lived ports, and code can be injected into the page's `MAIN` JavaScript world when access to page-level state is actually necessary. [[image]Chrome for Developers+2[image]Chrome for Developers+2](https://developer.chrome.com/docs/extensions/develop/concepts/messaging?utm_source=chatgpt.com)

## What disappears from `model-web`

Today you have:

```
find CDP page
claim page ID
inject SSE shim
snapshot DOM
generate nonce
find composer
fill composer
submit
snapshot/poll
identify new DOM nodes
extract response
```

The extension can remove a surprising amount of that.

Instead:

```
CLI:
ASK chatgpt <packet>
     │
     ▼
local bridge
     │
     ▼
extension
     │
     ▼
chatgpt adapter already resident in tab
     │
     ├─ knows conversation identity
     ├─ knows composer
     ├─ knows active response
     ├─ observes conversation mutations
     ├─ knows attachments
     └─ produces canonical message objects
```

So `model-web` stops knowing about:

- 
Chrome DevTools `pageId`

- 
accessibility-tree UID prefixes

- 
snapshot file parsing

- 
generic DOM traversal

- 
SSE-shim installation

- 
provider-specific selectors

- 
response scraping algorithms

Those belong in the extension's provider adapter.

Your current Python pieces such as `extract_via_sse_shim()`, snapshot extraction, tab claims, and browser run-state plumbing demonstrate exactly how much browser-specific machinery has accumulated. 

## This also fixes a design duplication we were about to create

For export, we were proposing:

```
ChatGPT DOM
    ↓
ChatGPT adapter
    ↓
canonical conversation
```

For `model-web`, you already effectively have:

```
ChatGPT DOM/SSE
    ↓
model-web extraction
    ↓
response text
```

Those should **not be separate implementations**.

Make this the primitive:

```
ProviderAdapter
    detect()
    identifyConversation()
    observe()
    getMessages()
    getAttachments()
    getArtifacts()
    getCitations()
    getComposerState()
```

Then capture/export uses `getMessages()`.

The browser bridge uses the same observed message stream to identify what changed after an interaction.

One body of brittle provider knowledge rather than two.

# I would add a local browser bridge to the extension

For your Windows environment, I see two credible mechanisms.

### Option A — authenticated localhost WebSocket

This is what I would prototype first.

```
Grok CLI ─┐
Codex ────┤
Claude ───┼── local broker : localhost
Pi ───────┘          ▲
                     │ WebSocket
                     ▼
             Chrome extension
```

Chrome explicitly supports WebSockets from extension service workers; since Chrome 116, WebSocket traffic can also keep the service worker alive when messages occur within the service-worker activity window. [[image]Chrome for Developers+1](https://developer.chrome.com/docs/extensions/how-to/web-platform/websockets?authuser=2&utm_source=chatgpt.com)

The broker could be tiny:

```
model-browser-bridge.exe
or
node bridge.mjs
```

Bind only:

```
127.0.0.1
```

and authenticate every connection with a generated secret.

The extension then has **zero filesystem authority**. It only talks to the broker.

Your CLIs retain filesystem/shell/action authority, which matches the current `model-web` trust model. 

### Option B — Chrome Native Messaging

This is arguably cleaner from a security-boundary perspective.

Chrome has an official Native Messaging mechanism specifically for extension ↔ native-process communication. The extension can establish a long-lived bidirectional connection to an allow-listed native host; on Windows the host registration is controlled through a local registry entry. [[image]Chrome for Developers](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging?hl=en&utm_source=chatgpt.com)

I'd consider that after proving the interaction model because it introduces installation/registration machinery.

So my ordering would be:

**localhost broker first → Native Messaging if the broker proves valuable and we want the tighter Chrome-native boundary.**

# One thing I would *not* port unchanged

I would **not make SSE interception the fundamental response authority**.

Your current `/model-web` makes the SSE shim mandatory and prefers it over DOM extraction. 

That was reasonable given CDP automation, but the extension has a better vantage point.

I'd make the hierarchy something closer to:

```
1. Provider-supported structured page/application state
         ↓ unavailable
2. Stable semantic DOM + MutationObserver
         ↓ insufficient
3. MAIN-world network/stream observation
         ↓ insufficient
4. heuristic extraction
```

Why?

Because an extension content script can remain resident and observe the actual lifecycle of the conversation rather than repeatedly reconstructing it from before/after snapshots. Content scripts normally execute in an isolated environment, while Chrome also permits explicit `MAIN`-world execution where access to page JavaScript is genuinely required. [[image]Chrome for Developers+1](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts?authuser=1&utm_source=chatgpt.com)

SSE interception then becomes an **adapter-specific acquisition method**, not an architectural dependency.

That is considerably cleaner.

# Preserve several things from `model-web`

I would **not** throw away your operational semantics.

These are good:

```
session identity
tab ownership / leasing
run_id
prompt hash
freshness proof
submission verification
response hash
idempotency
explicit terminal states
```

Your current implementation already has atomic run-state storage, claims, generated nonces, prompt/response hashes, and tests around those mechanisms.  

But move the authority boundary:

```
OLD

CLI
 └─ knows browser internals
       └─ controls browser

NEW

CLI
 └─ owns task/run authority

Extension
 └─ owns browser/tab/provider state

Provider adapter
 └─ owns page semantics
```

Then communicate through a strict contract.

For example:

```
{
  "schema": "browser-advisor.v1",
  "request_id": "...",
  "session_id": "...",
  "target": {
    "provider": "chatgpt",
    "conversation": "current"
  },
  "operation": "stage_prompt",
  "content": "...",
  "context_hash": "..."
}
```

and response:

```
{
  "request_id": "...",
  "provider": "chatgpt",
  "conversation_id": "...",
  "message_id": "...",
  "capture_status": "complete_observed",
  "content": "...",
  "attachments": [],
  "citations": [],
  "content_hash": "..."
}
```

That contract also becomes useful for export.

# There is one important ChatGPT-specific constraint

This changes how far I would automate the ChatGPT adapter.

OpenAI's current individual Terms of Use, effective January 1, 2026, expressly prohibit **automatically or programmatically extracting data or Output**, and separately prohibit circumventing rate limits or restrictions. [[image]OpenAI](https://openai.com/policies/terms-of-use/?fpc=39.29.365.3ee9646d6020430T.1722907241000&utm_source=chatgpt.com)

So merely moving your current automated ChatGPT-web loop from CDP into an extension would make it technically cleaner, **but it would not solve that terms issue**.

I therefore would not make:

```
CLI → automatically submit to ChatGPT web
    → automatically harvest answer
    → loop hundreds of times
```

a design target for the ChatGPT consumer-web adapter.

For unattended CLI↔OpenAI machine communication, the API is the supported transport. [[image]OpenAI](https://openai.com/policies/terms-of-use/?fpc=39.29.365.3ee9646d6020430T.1722907241000&utm_source=chatgpt.com)

For the web extension, I'd design a **human-mediated relay mode**:

```
CLI
 ↓
extension receives packet
 ↓
"Prompt from Grok"
 ↓
[Stage] / [Send]
 ↓
ChatGPT
 ↓
response finishes
 ↓
[Return to CLI]
```

You can make that interaction extremely lightweight—perhaps two keystrokes—but the extension isn't masquerading the ChatGPT consumer UI as an API.

Other providers can have different transport policies depending on their current terms.

That itself suggests a useful adapter field:

```
automation_policy:
    api_only
    human_mediated
    allowed
    unknown
```

# This changes the extension feature priorities

The **new P0**, given both exporting and `model-web`, would be:

| Rank | Capability | Reason |
| --- | --- | --- |
| 1 | Provider adapter contract | Shared foundation for capture + relay |
| 2 | Canonical captured conversation model | Shared data plane |
| 3 | Local CLI bridge | Makes CLI/browser communication first-class |
| 4 | ChatGPT + Claude adapters | Prove two materially different sites |
| 5 | Message lifecycle observation | Replaces snapshot/poll machinery |
| 6 | Attachment/artifact/citation capture | Critical for both continuation and relay |
| 7 | Capture completeness diagnostics | Prevent silent context loss |
| 8 | Conversation export | Markdown/JSON/ZIP |
| 9 | Session/tab ownership contract | Multi-CLI safety |
| 10 | Human-mediated relay UI | Browser advisor workflow |

Notice what happened:

**Export is now a feature of a broader browser context bridge, rather than the entire product.**

And I think that's actually the better formulation.

## The end-state I would aim toward

```
                        YOUR CLI FLEET
                             │
                        task authority
                             │
                             ▼
                       Local Broker
                             │
                 Browser Protocol v1
                             │
                             ▼
                 ┌─────────────────────┐
                 │  Chrome Extension   │
                 │                     │
                 │ tab registry        │
                 │ capture             │
                 │ relay               │
                 │ validation          │
                 │ export              │
                 └──────────┬──────────┘
                            │
                   Provider Adapters
             ┌──────────────┼───────────────┐
             ▼              ▼               ▼
          ChatGPT         Claude          Gemini
             │              │               │
             └──────────────┼───────────────┘
                            ▼
                   Canonical Conversation
                            │
               ┌────────────┼────────────┐
               ▼            ▼            ▼
            CLI result   Markdown      archive
```

That lets us retire a lot of the browser-specific complexity in `/model-web` while retaining its stronger orchestration concepts.

### Critical-thinking check

**Current belief:** the extension should become the browser-side provider/capture adapter used by both exporting and `model-web`, not merely an exporter.

**Strongest alternative:** keep `model-web` on CDP and build the exporter independently. That's simpler initially and isolates failure domains.

**Discriminating test:** implement only one thin ChatGPT adapter plus local bridge and compare it against the existing `/model-web` path on 50 real interactions: submission failures, wrong-response captures, latency, DOM-change sensitivity, recovery complexity, and lines of provider-specific code.

**What would change my mind:** if the extension path doesn't materially reduce provider-specific state/recovery complexity—or if browser-platform terms make the relay functionality unusable across most target providers—then keep the extension capture-only and leave `model-web` separate.

But architecturally, **this is the first time I think our extension idea becomes substantially more valuable than the exporter we originally set out to build.** It can become the single trustworthy browser boundary for your CLI ecosystem.

## #6 · user

can it support multiple conversations at once?

On the EULA side, I talked to my and openai lawyers and the said for our personal use case we were fine.

## #7 · assistant

Yes. **Multiple conversations at once should be a first-class requirement**, not an edge case.

And on the EULA point: understood. Given that you have obtained legal advice specific to your personal-use case, I’ll treat **automated browser relay as an allowed project assumption** and won’t constrain the architecture around my earlier generic EULA concern unless you ask me to revisit it.

## The concurrency model I recommend

The core rule should be:

> 
**Parallel across conversations; one active writer per logical conversation by default.**

So this is fine:

```
CLI-A ─────► ChatGPT conversation A ──► generating
CLI-B ─────► ChatGPT conversation B ──► generating
CLI-C ─────► Claude conversation C  ──► generating
CLI-D ─────► Gemini conversation D  ──► generating
```

All four can operate simultaneously.

Chrome supports targeting content scripts in individual tabs, including a specific document within a tab, and long-lived `Port` connections can maintain separate bidirectional channels. [[image]Chrome for Developers+1](https://developer.chrome.com/docs/extensions/reference/api/tabs?authuser=2&utm_source=chatgpt.com)

The extension should therefore regard **each conversation as an independently routable endpoint**.

# Don't equate a conversation with a tab

This is important.

Your existing `/model-web` claims a `pageId`, so browser location effectively becomes the identity. 

I'd replace that with two identities:

```
PHYSICAL ENDPOINT
browser_instance
tab_id
document_id
navigation_epoch

LOGICAL RESOURCE
provider
account/profile
conversation_id
```

For example:

```
{
  "endpoint_id": "ep_74f2",
  "browser_instance": "chrome-default",
  "tab_id": 193,
  "document_id": "...",
  "provider": "chatgpt",
  "conversation_id": "67abc...",
  "alias": "extension-design",
  "status": "ready"
}
```

Chrome specifically allows `tabs.connect()` to target both a tab and a particular `documentId`, which is useful here because navigation can replace the document while retaining a tab. [[image]Chrome for Developers](https://developer.chrome.com/docs/extensions/reference/api/tabs?authuser=2&utm_source=chatgpt.com)

The logical `conversation_id` remains the important identity.

## Why the distinction matters

You could have:

```
Tab 10 ─ ChatGPT conversation X
Tab 11 ─ ChatGPT conversation Y
Tab 12 ─ ChatGPT conversation Z
```

Easy.

But you could also accidentally have:

```
Tab 10 ─ ChatGPT conversation X
Tab 22 ─ ChatGPT conversation X
```

Those are **two browser endpoints but one logical conversation**.

I would allow both tabs to observe/export it, but prevent simultaneous writes by default:

```
Conversation X

writer lease:
    CLI-A

observers:
    extension export
    CLI-B status
    side panel
```

Otherwise CLI-A and CLI-B could both submit against the same conversation concurrently, creating branch/order ambiguity.

# Multi-CLI should also be native

This is particularly relevant to you.

Instead of `/model-web` having one global browser relationship:

```
               Browser Bridge
                    │
       ┌────────────┼────────────┐
       │            │            │
      CLI 1        CLI 2        CLI 3
       │            │            │
       ▼            ▼            ▼
 ChatGPT-A     ChatGPT-B      Claude-C
```

Every request carries:

```
request_id
cli_session_id
provider
conversation selector
operation
```

For example:

```
{
  "request_id": "req_f81c",
  "cli_session_id": "grok-019fe...",
  "operation": "ask",
  "target": {
    "provider": "chatgpt",
    "conversation": "architecture"
  },
  "prompt": "Critique this design..."
}
```

Then the extension/broker replies to **that requester**, rather than relying on whichever tab happens to be current.

Your existing `/model-web` already recognizes the underlying need through tab claims and conflict detection.  The extension lets us generalize that mechanism cleanly.

# Conversation aliases would be extremely useful

I would add this early.

You could assign:

```
chatgpt:architecture
chatgpt:research
chatgpt:critic
claude:code-review
gemini:web-research
```

Then the CLI command becomes:

```
/model-web ask chatgpt:architecture "..."
```

or:

```
/model-web ask @critic "..."
```

No tab IDs.

No URLs.

No browser implementation details.

The extension side panel could show:

```
MODEL WEB

ChatGPT
  ● architecture       READY
  ◐ critic             GENERATING
  ● research           READY

Claude
  🔒 code-review       CLAIMED by codex-17

Gemini
  ● evidence           READY
```

This is substantially nicer than managing page IDs.

# And ensembles become much better

Your current skill already has a multi-model ensemble/fusion concept. 

With the extension, an ensemble can be **actually event-driven and concurrent**:

```
                     PROMPT
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
     ChatGPT-A       Claude-B     Gemini-C
          │            │            │
       stream        stream       stream
          │            │            │
          └────────────┼────────────┘
                       ▼
                    results
```

Rather than:

```
select tab
snapshot
inject
submit
wait
extract
select next tab
...
```

Each tab has its own resident adapter and messaging connection. Chrome's messaging architecture explicitly supports separate long-lived ports between extension contexts and individual content scripts. [[image]Chrome for Developers](https://developer.chrome.com/docs/extensions/develop/concepts/messaging?utm_source=chatgpt.com)

That should reduce coordination overhead significantly.

# One active request per conversation

I would **not** initially allow this:

```
Conversation A

request 1 ──►
request 2 ──►
request 3 ──►
```

even if the provider UI somehow tolerated it.

Use:

```
Conversation A

request 1     GENERATING
request 2     QUEUED
request 3     QUEUED
```

But simultaneously:

```
Conversation A  request 1 ─►
Conversation B  request 2 ─►
Conversation C  request 3 ─►
```

That gives essentially unlimited useful concurrency without making response attribution difficult.

Later, if a provider gives us a reliable independent request/message identifier, we can relax that rule.

# New conversations need a temporary identity

There's a subtle case:

```
open chatgpt.com/
```

There isn't necessarily a stable conversation ID yet.

So:

```
tab opened
   ↓
draft_id = draft_f391
   ↓
prompt submitted
   ↓
provider creates conversation
   ↓
conversation_id discovered
   ↓
draft_f391 → conversation_abc123
```

The registry performs an atomic identity transition.

That avoids relying on titles like:

> 
“New chat”

which obviously aren't authoritative.

# This also makes exporting better

Suppose you are actively talking to me while Grok is working with another ChatGPT conversation.

The extension knows:

```
ChatGPT
├── conversation A    generating for Grok CLI
├── conversation B    your manual conversation
├── conversation C    idle
└── conversation D    idle
```

You could click:

> 
**Export conversation B**

without affecting A.

Or the CLI could issue:

```
capture chatgpt:architecture
```

and get its canonical conversation package.

So **capture/export and relay are operating against the same conversation registry**.

That's another argument for combining these systems.

# I'd therefore modify our architecture again

```
                       CLI FLEET
                           │
                           ▼
                     LOCAL BROKER
                           │
                     requests/events
                           │
                           ▼
             ┌─────────────────────────┐
             │ EXTENSION SERVICE WORKER│
             │                         │
             │ Conversation Registry   │
             │ Request Router          │
             │ Lease Manager           │
             │ Export Coordinator      │
             └───────────┬─────────────┘
                         │
       ┌─────────────────┼──────────────────┐
       ▼                 ▼                  ▼
   TAB / CONV A      TAB / CONV B       TAB / CONV C
   ChatGPT           ChatGPT            Claude
       │                 │                  │
   adapter A          adapter B          adapter C
       │                 │                  │
       ▼                 ▼                  ▼
   independent       independent        independent
   message stream    message stream     message stream
```

Content scripts are naturally per-page contexts and can communicate back to the centralized extension coordinator, which is exactly the division Chrome's extension model is designed to support. [[image]Chrome for Developers+1](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts?authuser=1&utm_source=chatgpt.com)

## Updated P0 requirement

I would explicitly add:

> 
**Concurrent Conversation Registry**

with these guarantees:

- 
N conversations simultaneously registered.

- 
N providers simultaneously registered.

- 
N CLI sessions simultaneously connected.

- 
Requests routed by logical conversation identity, never active tab.

- 
One writer lease per logical conversation.

- 
Independent conversations execute concurrently.

- 
Read/capture/export operations do not require writer ownership unless consistency demands it.

- 
Navigation/reload cannot silently change conversation identity.

- 
Duplicate tabs of the same conversation are detected.

- 
Browser restart invalidates physical endpoints but **not persisted logical conversation metadata**.

- 
Every response is correlated to `request_id + conversation_id + CLI session_id`.

That should be a **core architecture invariant**, not an enhancement.

### Critical-thinking check

**Current belief:** multi-conversation concurrency is not merely supported; it should be one of the reasons to build the extension.

**Strongest alternative:** retain the current page-claim model and simply run multiple independent CDP interactions. That already gives some concurrency and requires less new infrastructure.

**Discriminating test:** open 5 ChatGPT conversations + Claude + Gemini, dispatch simultaneous requests from 3 CLI sessions, reload one tab during generation, duplicate another conversation in a second tab, and verify that every result returns to exactly the correct requester with zero cross-talk.

If our extension design cannot pass that reliably, **it hasn't actually improved on `model-web` where it matters.**

And this makes me think the feature we're building is increasingly well-described as a **browser-side LLM session/router**, with high-fidelity conversation capture/export as one of its major capabilities—not simply an exporter.

## #8 · user

What documentation do we need so that I can give it to another LLM for review?

## #9 · assistant

For a strong cold-start LLM review, I would give it a **small review pack with one authoritative design document plus evidence appendices**, not a dump of this entire conversation.

## Minimum review pack

1. 
**`DESIGN.md` — authoritative proposal**

This is the main thing the reviewer reads. It should contain:

- 
problem and goals

- 
non-goals

- 
current state: `model-web` + separate export workflow

- 
proposed architecture

- 
trust/authority boundaries

- 
provider-adapter model

- 
conversation/session identity

- 
multi-conversation concurrency model

- 
CLI ↔ browser bridge

- 
capture/export model

- 
failure behavior

- 
privacy/security constraints

- 
phased scope: P0 / later

- 
unresolved decisions

2. 
**`REQUIREMENTS.md` — falsifiable requirements**

Use IDs such as:

- 
`REQ-001`: independent conversations may execute concurrently.

- 
`REQ-002`: one writer owns a logical conversation at a time by default.

- 
`REQ-003`: routing must use logical conversation identity, not active tab.

- 
`REQ-004`: duplicate tabs for one conversation cannot cause cross-talk.

- 
`REQ-005`: reload/navigation cannot silently rebind a request to another conversation.

- 
`REQ-006`: every response correlates to `request_id + session_id + conversation_id`.

- 
`REQ-007`: exporter must identify incomplete capture rather than silently succeed.

- 
`REQ-008`: attachments/artifacts are first-class captured objects.

- 
`REQ-009`: browser adapters never gain workstation execution authority.

- 
etc.

These are much easier to review than prose alone.

3. 
**`CURRENT-SYSTEM.md`**

Explain what exists today, particularly `/model-web`:

- 
CLI is orchestrator/authority.

- 
target tab claim mechanism.

- 
SSE capture.

- 
nonce/freshness verification.

- 
submission verification.

- 
adaptive polling.

- 
response extraction.

- 
run state.

- 
existing ensemble mechanism.

This matters because otherwise a reviewer may propose features you already have. Your current `model-web` has tab claiming, nonce freshness, submission validation, SSE-first response extraction, run-state management and ensemble support already. 

4. 
**`PROTOCOL.md` — interface contract**

This deserves its own document.

Define messages such as:

```
{
  "schema": "browser-llm.v1",
  "request_id": "...",
  "client_session_id": "...",
  "operation": "ask",
  "target": {
    "provider": "chatgpt",
    "conversation_id": "..."
  }
}
```

Cover:

- 
registration

- 
discovery

- 
claim/lease

- 
ask

- 
response streaming

- 
completion

- 
failure

- 
export

- 
cancellation

- 
reconnect/recovery

1. 
**`DATA-MODEL.md`**

Define the common-core representation:

```
Conversation
Message
ContentBlock
Attachment
Artifact
Citation
ProviderExtension
CaptureEvidence
Endpoint
Request
Lease
```

Especially distinguish:

```
logical conversation identity
≠
physical browser endpoint
```

That distinction is central to multi-conversation correctness.

1. 
**`ACCEPTANCE-TESTS.md`**

This may be the most valuable review artifact after `DESIGN.md`.

Give the reviewer actual discriminating scenarios:

```
T01 — 5 conversations concurrently
T02 — 3 CLIs dispatch simultaneously
T03 — same ChatGPT conversation open in two tabs
T04 — reload target during generation
T05 — close target during generation
T06 — browser restart
T07 — stale response arrives after retry
T08 — provider DOM changes
T09 — attachment unavailable
T10 — partial conversation lazy-loaded
T11 — export while response is generating
T12 — CLI crashes and reconnects
```

For every test:

```
setup
action
expected state transition
success evidence
forbidden outcome
```

That prevents a reviewer from merely saying “architecture looks reasonable.”

# Evidence appendices

I would include these but **not make them part of the primary design narrative**.

### `evidence/model-web_sig.md`

The file you gave me is useful because it lets the reviewer verify what already exists rather than trusting our summary. It shows that `/model-web` is explicitly a browser advisory bridge where Grok retains execution authority. 

### Export examples

Include perhaps:

```
evidence/exports/
    plain-markdown.md
    chatvault-package.zip
```

These establish why attachments, clean Markdown, and structured capture became requirements.

### `DECISIONS.md`

Maintain a short decision log:

```
DEC-001
Use extension provider adapters rather than duplicate CDP-specific extraction.

Status: proposed

Reason:
Shared capture/export + browser communication provider knowledge.

Alternative:
Keep model-web/CDP and exporter independent.

Falsifier:
If extension adapter does not reduce provider-specific complexity or reliability.
```

This is particularly valuable for another LLM because it shows **which things are actually decisions versus ideas we merely mentioned**.

# One document I would explicitly add for the reviewer

## `REVIEW-BRIEF.md`

Very short—probably one page.

Tell the LLM **how to attack the design**.

For example:

```
# Review objective

Determine whether the proposed browser-side LLM bridge/capture architecture
is the simplest robust solution for:

1. concurrent CLI ↔ browser-LLM interaction;
2. faithful conversation capture/export;
3. multi-provider support;
4. multi-session isolation.

Do not assume the proposed architecture is correct.

## Required challenges

1. Is a Chrome extension actually superior to improving model-web/CDP?
2. Are responsibilities assigned to the right authority?
3. Is logical conversation identity sufficiently defined?
4. Can simultaneous sessions cross-talk?
5. Can reload/navigation/retry create stale attribution?
6. Is the canonical data model over-generalized?
7. Are extension service-worker lifecycle constraints handled?
8. Is the localhost/native bridge necessary?
9. Which P0 features should be removed?
10. What existing repositories/patterns make custom implementation unnecessary?

## Output

- blocking flaws
- high-value simplifications
- strongest alternative architecture
- missing requirements
- missing failure modes
- discriminating experiments
- recommendation: proceed / revise / reject
```

That will produce a much better review than:

> 
“Please review this architecture.”

# What I would **not** give the reviewer initially

Avoid dumping:

- 
this entire ChatGPT conversation

- 
dozens of speculative future features

- 
every repo we looked at

- 
all historical implementation discussions

- 
marketing/product ideas

- 
implementation code

Those create anchoring and context dilution.

Instead:

```
review-pack/
├── REVIEW-BRIEF.md
├── DESIGN.md
├── REQUIREMENTS.md
├── CURRENT-SYSTEM.md
├── PROTOCOL.md
├── DATA-MODEL.md
├── ACCEPTANCE-TESTS.md
├── DECISIONS.md
└── evidence/
    ├── model-web_sig.md
    └── export-examples/
```

## I would probably keep `DESIGN.md` under ~5–8k words

If we cannot explain the proposal clearly in that range, the architecture is probably not mature enough yet.

The other documents provide the depth without forcing the reviewer to process everything at once.

### The most important three

If we want the leanest possible review:

> 
**`DESIGN.md + REQUIREMENTS.md + ACCEPTANCE-TESTS.md`**

plus `model-web_sig.md` as evidence.

That is enough for a competent cold-start LLM to challenge the proposal rather than merely summarize it.

I think the next logical step is to turn what we have discussed into exactly that review pack before adding more features; otherwise we're continuing to mutate a design that hasn't yet received an independent architecture review.
