---
title: "Here's a chat with C.ai, about CC.  Do you have any suggestions?
'I don't like this:
'✻ Cogitated for 32s
❯ 4. LLM Advis"
date: "2026-02-09"
mode: "CONCISE"
uuid: "e68ce1a0-c312-4373-a449-63a8d3f6fca5"
entry_count: 2
---

## Human

Here's a chat with C.ai, about CC.  Do you have any suggestions?
"I don't like this:
"✻ Cogitated for 32s
❯ 4. LLM Advisory Pilot
What: LLM-based advisory layer for explainability and nuance

Use case: More nuanced block explanations, ambiguous case analysis

Decision gate:
- ✅ Go: Deterministic layer has high ambiguity and explainability gaps
- ❌ No-Go: Latency/cost exceeds budget or advice quality low

Solo-dev consideration: This would call an LLM during hook execution. Adds latency (seconds) and

cost. Only
for explainability—never authoritative for blocking., I'm not sure you are right. Where's your
evidence?
● You're right to challenge this. Let me check the actual plan documentation for evidence about LLM advisory
latency/cost specifications.
● Searched for 1 pattern, read 1 file (ctrl+o to expand)
● You're right. I made claims without evidence from the plan document.
What the plan actually says:
Line 86 (Go/No-Go Matrix): "Latency/cost exceeds budget or advice quality low" → No-Go signal
Line 228: "LLM advisory pilot with strict latency/cost budgets"
Line 272: Mitigation: "enforce strict per-layer latency budgets"
What I claimed (without evidence):
"Adds latency (seconds)" ❌ Not in the document
Specific cost figures ❌ Not in the document
What the plan actually specifies:
p95 stop-hook latency target: < 200ms (lines 196, 252)
The plan says "strict latency/cost budgets" but does not specify what those budgets are
Corrected assessment:
The plan defers LLM advisory by default, with a go/no-go decision based on whether:
The deterministic layer has "high ambiguity and explainability gaps" (need)
Latency/cost would "exceed budget" (risk)
But the plan does not specify:
What the LLM advisory latency budget is
What "exceeds budget" means in practice
Whether seconds are acceptable or not
I was speculating. The actual evidence only shows that LLM advisory is optional, requires strict budgets,
and must demonstrate benefit over the deterministic layer. The specific budget numbers are not defined in
the plan.
Thank you for the correction."
speculating without data is leading to bad decisions. How can we prevent this without creating a lot of friction?
Show less
HookSessionStart:startup
HookSessionStart:startup
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n[Lock Cleanup] Removed 6 stale lock(s) from previous session(s).\n\n\ud83d\ude80 Semantic daemon ready: \\\\.\\pipe\\csf_semantic_39868_1770615691 (0ms)"}}
Good question. The core problem is: the model generates plausible-sounding claims (like "adds latency (seconds)") without grounding them in evidence, and this happens silently — no signal that it's speculating until challenged.
Low-friction options:
1. Confidence tagging convention — When making claims about system behavior, cost, or performance, tag them:
[EVIDENCED: file:line] — grounded in something read
[ESTIMATED] — reasonable inference, not verified
[SPECULATIVE] — no evidence
This is zero-tooling cost — just a CLAUDE.md instruction. The model already knows when it hasn't read a file.
2. A short CLAUDE.md rule — Something like:
When making quantitative claims (latency, cost, size, frequency) or behavioral claims (what code does, how systems work), cite the source. If no source was consulted, say "unverified" rather than stating as fact.
This is ~2 lines in CLAUDE.md and addresses the specific failure mode without adding process.
3. Strengthen the existing hook — Your UserPromptSubmit hook already emits FALSIFY: behavior claims → read code before asserting. The problem is this fires on every prompt and gets ignored. A more targeted approach: only fire when the model's previous response contained uncited claims. But that requires parsing output, which adds complexity.
My recommendation: Option 2 — a CLAUDE.md rule. It's the lowest friction, directly addresses the failure, and works because the model does know when it hasn't looked at evidence. The problem isn't capability, it's that nothing told it to stop and flag the gap."

## Assistant

You’re already very close: the problem isn’t capability, it’s that the system gives the model no *cost* for speculating and very little *affordance* for “I don’t know.” The fix is small, local guardrails in exactly the spots where speculation hurts.

### 1. Tighten the norm, not the process

Instead of “confidence tags everywhere,” encode one very specific, low-friction rule in CLAUDE.md:

> When making claims about latency, cost, throughput, or what code/config “says,” you must either (a) cite an inspected source (file:line, tool output, or user message), or (b) explicitly label the claim as “unverified estimate.”

This leverages a known pattern: LLMs produce better calibrated verbal confidence when explicitly asked to state it, compared to using raw probabilities alone. You’re just baking that pattern into the house style.[1]

Impact:

- No new tools, hooks, or parsing.
- It does not forbid speculation; it forces spec to be *visibly* spec.
- It localizes friction only to the risky classes of claims (perf, cost, behavior).

### 2. Add a tiny self-check habit

Give it one more micro‑rule for revisions and “you’re wrong” moments:

> If you revise a previous claim after checking evidence, include a 2–3 line “Correction block” that:
> - Names the original claim.
> - States what evidence you checked.
> - States what is now known vs still unknown.

This is basically structured “self‑refinement through feedback,” which is one of the standard hallucination‑mitigation patterns for LLMs. You already see it doing this ad hoc in the snippet you pasted; you’re just formalizing the shape so it’s reliable and compact instead of rambly.[2]

Example (what you want consistently):

> **Correction:** I previously said “adds latency (seconds).”  
> Evidence: plan.md lines 86, 196, 228, 252.  
> Now known: strict budgets are required; p95 stop-hook target < 200ms is defined; the exact LLM budget is not specified. “Seconds” was an unverified estimate.

That’s ~3 lines, low friction, and it trains a habit of clearly marking the boundary between fact and guess.

### 3. A single, focused hook tweak

Your current “FALSIFY: read code before asserting” hook fires constantly and becomes noise. To keep friction low but make it *bite* where it matters, narrow its trigger:

- Only fire when:
  - The new message contains quantitative or behavioral claims **and**
  - The previous message from the model has at least one “unverified estimate” (or no citations) about the same object (plan file, hook, etc).

You don’t even need full AST-level parsing; a cheap heuristic (regex for “ms”, “seconds”, “cost”, “latency”, “budget”, “throughput” plus filename mentions) is enough to catch most of these. This mirrors “automatic evidence selection” ideas, which focus intervention only when a claim is unsupported by retrieved evidence.[3]

Hook copy could be extremely short:

> You are making new performance or cost claims about X without citing a source and after previously giving unverified estimates. Before continuing, inspect the relevant file(s) and either:
> - Cite concrete lines, or
> - Explicitly mark the claim as “unverified estimate.”

This is still low friction: it only trips in exactly the failure mode you care about, and the remediation path is short and obvious.

### 4. Don’t let “seconds” sneak in as a default prior

You can also nudge its prior away from “LLM = seconds” by encoding the specific reality of your stack:

- Add a short note in CLAUDE.md or the plan:

> In this system, budgeted stop-hook latency is sub-200ms; LLM calls are experiments that must fit within strict per-layer budgets, not “seconds-long” by default.

That helps override the generic prior that LLM invocations are slow, which is a known source of hallucinated performance claims when domain-specific constraints aren’t explicit.[4]

***

If you want, I can draft the exact CLAUDE.md diff and a minimal regex-based detector for “risky claims after unverified estimates” that you can wire into your existing hook without changing the rest of your pipeline.

## Human

yes please

## Assistant

Here’s a concrete CLAUDE.md diff plus a minimal detector idea you can drop into your hook layer.

***

## CLAUDE.md diff (spec vs evidence)

You can adapt naming, but this keeps it tight and local to the failure mode.

```diff
 ## House rules for CC assistant

 +### Evidence vs speculation
 +
 +When you talk about how the system behaves, you must distinguish **evidence** from **guessing**:
 +
 +1. For any claim about:
 +   - latency, cost, throughput, budgets, or limits
 +   - what code, configs, or plan documents say
 +   - whether a feature “does” or “will” behave a certain way
 +   you must do one of:
 +   - Cite a concrete source: `plan.md:86`, `hooks/stop.ts:120`, or a user message; or
 +   - Explicitly mark the claim as an **unverified estimate**.
 +
 +2. Never present an unverified estimate as a fact.
 +   - Bad: `This will add latency (seconds).`
 +   - Good: `Unverified estimate: this likely adds noticeable latency per call (order of magnitude: hundreds of ms), but the plan does not define an exact budget.`
 +
 +3. When you revise yourself after checking evidence, include a short **Correction** block:
 +   - Name the original claim.
 +   - State what you checked (file + lines, or tool output).
 +   - State what is now known vs still unknown.
 +
 +Example:
 +> Correction: I previously said "adds latency (seconds)".  
 +> Evidence checked: `plan.md` lines 86, 196, 228, 252.  
 +> Now known: strict budgets and a `< 200ms` stop-hook target are defined; the LLM advisory latency budget is not specified. My earlier "seconds" claim was an unverified estimate, not supported by the document.
 +
 +If you cannot find evidence, say so plainly instead of guessing.
```

This embeds a simple “evidence supremacy” norm similar to other prompt templates that force models to label speculative vs grounded reasoning, which has been shown to reduce hallucinations without heavy tooling.[1][2]

***

## Minimal “risky claim after guess” detector

You can bolt this onto your existing `UserPromptSubmit` / `ModelOutput` hooks. Pseudocode in TypeScript-ish style for the hook process that inspects the last assistant message and the new one:

```ts
// Heuristic keywords that usually indicate perf/cost claims
const PERF_TERMS = [
  "latency",
  "throughput",
  "p95",
  "p99",
  "ms",
  "milliseconds",
  "seconds",
  "s/",
  "per second",
  "budget",
  "cost",
  "token cost",
  "rate limit",
  "qps",
  "rps",
];

function containsPerfClaim(text: string): boolean {
  const lower = text.toLowerCase();
  return PERF_TERMS.some(term => lower.includes(term));
}

function containsUnverifiedMarker(text: string): boolean {
  const lower = text.toLowerCase();
  return lower.includes("unverified estimate")
      || lower.includes("unverified")
      || lower.includes("speculative");
}

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

interface HookContext {
  conversation: Message[];
}

export function shouldNudgeForEvidence(ctx: HookContext): boolean {
  const msgs = ctx.conversation;
  const lastAssistant = [...msgs].reverse().find(m => m.role === "assistant");
  const lastUser = [...msgs].reverse().find(m => m.role === "user");

  if (!lastAssistant || !lastUser) return false;

  const prev = lastAssistant.content;
  const current = lastUser.content;

  // Only trigger if:
  // 1) Assistant previously made perf/cost claims
  // 2) They were not explicitly marked "unverified"
  // 3) User is now asking follow-ups (challenge/clarification)
  if (!containsPerfClaim(prev)) return false;
  if (containsUnverifiedMarker(prev)) return false;

  const challengeish = ["evidence", "source", "where", "why", "prove", "are you sure"];
  const lc = current.toLowerCase();
  const userIsChallenging = challengeish.some(t => lc.includes(t));
  if (!userIsChallenging) return false;

  return true;
}
```

If `shouldNudgeForEvidence` returns true, you prepend/append a short, opinionated system hint to the *next* assistant turn:

```ts
const EVIDENCE_NUDGE = `
You previously made claims about latency/cost or budgets without citing evidence.
Before you answer this user message:

1. Inspect the relevant plan/code/config files as needed.
2. Either:
   - Cite specific lines for any concrete claims, or
   - Mark them explicitly as "unverified estimate".

If the documents do not define a number or budget, say that clearly instead of guessing.
`.trim();
```

Wire it into your hook something like:

```ts
if (shouldNudgeForEvidence(ctx)) {
  messages.unshift({
    role: "system",
    content: EVIDENCE_NUDGE,
  });
}
```

This is intentionally minimal:

- No JSON schemas, no chain-of-verification; it just nudges the model at the exact moment it’s likely to speculate again.
- It pairs with the CLAUDE.md rule so the model has a clear remediation path.
- It relies on lightweight heuristics similar to other “prompt-level hallucination mitigations” rather than heavy evaluation.[3][4]

If you share your current hook signature (what the CC extension receives on each event), I can translate this into exact code for your environment.
