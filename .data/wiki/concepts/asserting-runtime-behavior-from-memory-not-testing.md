---
title: "Asserting Runtime/Platform Behavior From Memory Instead of Testing It"
created: 2026-07-31
source: session-20260730
tags: [behavioral-pattern, premature-closure, platform-behavior, verification, assert-before-investigate, narrative-before-evidence, operator-correction]
summary: >
  The agent asserted "reloading a Chrome extension doesn't reload the sidepanel"
  as fact, from training-data memory, without any tool call to verify. When the
  operator pushed back, the agent investigated and found it didn't know the
  actual cause. The fix: any claim about how a browser, platform, CLI, runtime,
  or library BEHAVES must either be backed by a test/observation in the current
  session, or labeled [INFERENCE] / [UNKNOWN]. Asserting untested runtime
  behavior as fact is the sharpest, most dangerous form of premature closure —
  it closes investigation before it starts.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - session-20260730 (operator correction: "we must kill this behavior")
relations:
  - target: wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md
    type: sharpens — this is the specific instance where the "plausible narrative" is about runtime/platform behavior
  - target: wiki/concepts/narrative-as-signal-anti-dismissal-rule.md
    type: extends — applies the "construct a narrative for why X can't be done → investigate" rule to the inverse case (narrative for why X IS a certain way)
  - target: wiki/concepts/trust-over-believability.md
    type: instance-of
---

# Asserting Runtime/Platform Behavior From Memory Instead of Testing It

## The pattern

The agent makes a confident claim about how a specific tool, platform, browser,
or runtime behaves — stated as `[FACT]` without any verification receipt in the
current session. The claim comes from training data or prior-session memory,
not from a test performed this turn.

**Example (this session):** The operator said buttons weren't appearing after
reloading the Chrome extension. The agent responded: "reloading the extension
restarts the service worker but does not reload an already-open sidepanel page."
This was stated as fact. When the operator challenged it ("Are you sure because
I don't believe you"), the agent investigated, found the patched code was
correctly in the loaded file, and admitted: "I was guessing about Chrome's
reload behavior."

## Why it's dangerous

This is the sharpest form of [[premature-closure-narrative-sufficiency-external-approaches]].
When the narrative is about *code logic* or *system design*, the operator can
often spot the error because they know the system. When the narrative is about
*runtime/platform behavior*, the operator may not know either — and a confident
wrong assertion sends both the agent and the operator down the wrong path.

In this session, the wrong assertion ("reload doesn't reload the sidepanel")
would have sent the operator on a wild goose chase of closing/reopening
panels, when the actual issue might be a DOM-search failure in the injection
code — a completely different problem.

## How to detect it

The pattern fires when the agent is about to state a claim about:
- How a browser handles extensions, tabs, rendering, CSP, service workers
- How a CLI tool behaves with specific flags or inputs
- How a library/runtime resolves paths, enforces boundaries, or processes input
- How an OS handles files, processes, permissions, networking
- How a protocol (MCP, ACP, WebSocket, HTTP) behaves in edge cases

**The test:** "Did I test this in the current session, or am I recalling it
from training data?" If the answer is training data, the claim must be labeled
`[INFERENCE]` or tested before asserting.

## The fix

**Structural:** Any claim about runtime/platform behavior must be:
1. **Tested in-session** (tool call that demonstrates the behavior), OR
2. **Labeled `[INFERENCE]`** with the uncertainty exposed, OR
3. **Labeled `[UNKNOWN]`** and investigated before continuing

This is already in the AGENTS.md evidence-tier system (reading code = Tier 3,
not Tier 1; running commands = Tier 1). But the pattern slips through because
the claim isn't about code the agent is reading — it's about runtime behavior
the agent is *recalling*. The evidence-tier system doesn't explicitly cover
"recalling platform behavior from training data" as a distinct, lower tier.

**Proposed tier addition:** Training-data recall of runtime/platform behavior
is **Tier 4 (50%)** — same as "comments, unverified claims, speculation." It
cannot be stated as `[FACT]` without a verification receipt.

**Behavioral mitigation:** Before asserting any platform-behavior claim, the
agent should ask: "Could I be wrong about this? What's the cheapest way to
test?" — the standard falsifier question from the thought-partner protocol,
but applied specifically to runtime-behavior claims where the agent's
confidence comes from familiarity rather than evidence.

## Connection to existing patterns

This is a sharpening of several existing concepts:
- [[premature-closure-narrative-sufficiency-external-approaches]] — the parent
  pattern; this is the specific instance where the "plausible narrative" is
  about how a platform/runtime behaves
- narrative-as-signal-anti-dismissal-rule — applies the inverse: when you
  construct a narrative for "why X can't be done," that's a signal to read
  docs. Here, constructing a narrative for "why X is behaving this way" should
  be a signal to test, not assert.
- [[trust-over-believability]] — the operator's trust is eroded by confident
  wrong assertions more than by honest uncertainty

## Falsifier

This concept is wrong if, in practice, the agent's training-data recall of
platform behavior is reliable enough that labeling it `[INFERENCE]` creates
excessive overhead without preventing real errors. Test: track how often
training-data platform-behavior claims are correct vs wrong over 10
instances. If >90% correct, the labeling requirement may be over-engineering.
If <70% correct, it's essential.
