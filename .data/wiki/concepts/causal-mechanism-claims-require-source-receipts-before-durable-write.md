---
title: "Causal mechanism claims require source inspection before durable write"
created: 2026-07-25
source: session-019f96f5
tags: [receipt-rule, causal-claims, durable-write, wiki-authoring, failure-mode, anti-fabrication, cross-host]
summary: >
  The general "Claims require receipts" rule (AGENTS.md) already forbids
  presenting inference as fact. This concept adds a specific high-risk
  surface form: when writing a CAUSAL MECHANISM claim ("X happens because
  the scanner greps the parent transcript") into a DURABLE artifact (wiki
  concept, handoff, commit message, ADR), the agent must READ THE SOURCE
  before writing — not infer the mechanism from observed behavior and
  present the inference as the mechanism. The falsifier is the operator
  asking "explain clearly" or "what's your evidence": if the agent's
  response would require reading the source for the first time, the
  original claim was inference presented as fact. Worked example (the
  incident that surfaced this rule, 2026-07-25): agent wrote a wiki concept
  claiming the close scanner "can't see /check subagent transcripts"
  (mechanism) based on observing that the scanner reported a verification
  gap despite /check running. Operator asked "explain clearly." Agent read
  close_accounting.py for the first time and discovered (a) the mechanism
  claim was correct (lines 422-510 read only parent transcript), but (b)
  the related claim that "verifiers ran tests" was wrong (verifiers ran
  git/static checks, not pytest). The mechanism half survived; the
  worked-example half collapsed. The pattern: inferring mechanism from
  behavior is sometimes right and sometimes wrong, and the agent cannot
  distinguish without reading the source. Fix: source-inspection receipt
  BEFORE the durable write, not after operator pushback. Trigger: about
  to write "X happens because <mechanism>" into a wiki concept, handoff,
  or commit message → stop and read the source first. If you can't cite
  line numbers, you don't have the receipt.

## Sub-pattern: vocabulary-mismatch grep fallacy (added 2026-07-26)

A specific failure mode within the general pattern: **grepping with the searcher's vocabulary instead of the source's vocabulary, then treating the null result as evidence of absence.**

**How it manifests:** the agent wants to write a claim about how a workspace skill works ("`/close` does not auto-invoke `/aar`"). It greps the source file using its own framing vocabulary ("blind", "gap", "filter"). The grep returns results — but only for sections that share the searcher's vocabulary. Sections that cover the same function under different vocabulary (e.g., `/close` frames it as the "Retrospective gate" using "auto-invoke") don't match. The agent treats "my grep didn't return it" as "it's not there" — a classic absence-of-evidence fallacy.

**Why it's dangerous:** the grep *feels* thorough because it returns multiple matches. The agent has "evidence" (16 lines returned!) and uses that evidence to license a confident claim. The evidence is real but incomplete in a way the agent can't detect without either (a) broadening the vocabulary or (b) reading the section directly.

**Reference incident (2026-07-26, session 019f9bfe):** I grepped `/close/SKILL.md` for `blind|missing|forgot|gap|filter` while writing `blind-spot-detection-methods.md`. The grep returned 16 lines (genuine matches). I concluded `/close` doesn't auto-invoke `/aar`. Line 123 — which explicitly says "auto-invoke `/aar` — do not recommend it, run it" — didn't match my pattern because it uses "retrospective" and "auto-invoke," not "blind" or "gap." The operator caught it; the wiki concept had to be corrected.

**Structural fix (beyond the general rule):** when grepping a source to verify a claim about its behavior, run TWO searches:
1. The searcher's vocabulary (your framing)
2. The source's likely vocabulary (the skill/function names, the verbs the source uses)

If search #1 returns results but search #2 returns different results, the vocabulary mismatch is the signal — read the section directly before claiming absence. This is the receipt: two searches with different vocabularies, both confirming or both refuting.

**Three instances in session 019f9bfe:** crawl4ai upgrade (didn't grep wiki for "crawl4ai upgrade"), `/tp quick` misrecommendation (didn't read the skill's actual mode definitions), `/close`-`/aar` (this incident). The pattern recurs despite the rule existing — confirming the rule's own warning that behavioral mitigations decay under closure pressure.

## Sub-pattern: receipt misattribution across neighboring claims (added 2026-07-26b)

A specific failure mode within the general pattern: **verifying a neighboring claim (e.g., discovery — "tools scan directory D") and misattributing that receipt to license a different claim (e.g., deployment — "tools will handle symlinked entries into D correctly").** The agent has a real receipt, but for the wrong claim. The receipt's surface features (docs cited, sources scored) license the confident endorsement, but every piece of evidence verifies something other than the claim being endorsed.

**How it manifests:** the agent researches and verifies claim A (e.g., "tools X, Y, Z scan directory D"). It then recommends a deployment pattern as a side-conclusion based on claim B (e.g., "symlink into D to cover X/Y/Z"). Claim B is never independently tested — it inherits the rigor of claim A's verification. The recommendation ships as "Option 1 (recommended)" with the implicit assumption that "documented scan root" = "correctly handles edge cases." Both the discovery and the recommendation feel complete because the surface features of rigor (citations, alternatives, falsifier) are present — but they all verify claim A, not claim B.

**Why it's dangerous:** the receipt is REAL. The agent has "evidence" (docs say the tool scans D!) and uses that evidence to license a confident deployment endorsement. The evidence is real but for a different claim than the one being endorsed. This is harder to catch than pure fabrication because the citation chain is valid — the failure is in *which claim* the citation supports.

**Reference incident (2026-07-26b, session 019f9f48):** I researched whether `~/.agents/skills/` is polled by major agent CLIs (claim A — discovery; verified via OpenCode docs, Codex issues, Grok Build session list — Tier 2/1 receipts, valid). I then recommended "single symlink from P:/.agents/skills/ to ~/.agents/skills/ covers 4/5 environments in one shot" as the Option 1 deployment pattern (claim B — never tested, never even surfaced as a separate claim). Two turns later, the operator asked the right question — "does this cause duplication?" — and research showed EVERY major tool (OpenCode, Codex, Copilot, Claude Code, Grok Build) has open bugs documenting exactly this dedup-failure class. The recommendation collapsed. The wiki concept I refined in the same turn encoded the broken pattern as "recommended" — a durable write of an unverified behavioral claim licensed by receipt misattribution.

**Three layers of the failure (diagnostic spine):**
- **MODEL BEHAVIOR (closure pressure):** the recommendation flowed as a "natural follow-on" to a refutation, which felt like enough work was done. The refutation completed the discovery claim; the deployment recommendation rode its momentum.
- **WORKFLOW (no gate):** no rule fires for "deployment recommendations require their own verification, separate from the discovery claim that motivated them."
- **ARCHITECTURE (rule scope too narrow):** the Capability Claims rule (`~/.grok/AGENTS.md` § "Capability Claims") covers "CLI flags and API params" but does NOT cover behavioral claims about how tools will respond when configured a specific way. Deployment patterns fall through the rule's scope.

**Structural fix (beyond the general rule):**

When a research output (any `/www`, `/web`, or chat turn) produces a DEPLOYMENT, INSTALL, or CONFIGURATION recommendation spanning multiple tools:
1. **Receipt required:** the recommendation must be backed by either (a) a direct test in ≥1 tool (Tier 1), OR (b) explicit `[INFERENCE]` labeling with a named discriminating test that would resolve it.
2. **Durable-write gate:** if the recommendation is written into a wiki concept, handoff, or commit message, the concept MUST label the recommendation as `[INFERENCE]` until a test receipt exists. "Option 1 (recommended)" without a test receipt is forbidden.
3. **Rule broadening:** amend `~/.grok/AGENTS.md` § "Capability Claims" to read: *"CLI flags, API params, and behavioral claims about how a system will respond when configured or deployed a specific way are hypotheses until verified with `--help`, a live check, or empirical test."*

**Falsifier (replacing the original counterfactual):** the (test OR label) binary test above. A deployment recommendation is safe to ship only if it satisfies (a) OR (b). If neither, the recommendation must be downgraded to a hypothesis. This is mechanically checkable, not counterfactual introspection.

**Receipts:**
- **Turn 1 of session 019f9f48** contained "Option 1 (recommended): single source at P:/.agents/skills/, deploy via symlink to ~/.agents/skills/" with only "[INFERENCE] One-time setup cost" tagged — the deployment-behavior claim was unlabeled. [OBSERVED] `C:/Users/brsth/.grok/sessions/P%3A%5C/019f9f48-5ad0-7a01-9f1e-e70d0788d383/chat_history.jsonl` turn 1 assistant response.
- **Turn 3 of the same session** showed open dedup-failure bugs in OpenCode (`anomalyco/opencode#29950`, `#32202`), Codex (`openai/codex#25324`, `#8169`), Copilot (`vercel-labs/skills#1200`), Claude Code (`anthropics/claude-code#10115`, `#46833`, `#42384`), and Grok Build (observed locally). [OBSERVED] same transcript turn 3.
- **The discovery claim was correctly verified** — OpenCode docs at `opencode.ai/docs/skills/` do list six scan paths including `~/.agents/skills/`. [OBSERVED] same transcript turn 1. The receipt was real; it was misattributed to the deployment claim.

## Receipts (for the vocabulary-mismatch sub-pattern)

- **`_has_code_writes` was `.py`-only before this session's fix** — [OBSERVED] `C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py:400-409` (pre-fix version). The function filtered for `.py/.pyw/.pyx/.pyi/.pxd` only; `.md` wiki writes were not counted as substantive work.
- **`/close` auto-invokes `/aar` when Retrospective gate is `needs_attention`** — [OBSERVED] `C:\Users\brsth\.grok\skills\close\SKILL.md:123`. The grep for "blind|gap|filter" didn't match because line 123 uses "retrospective" and "auto-invoke" — the vocabulary mismatch this sub-pattern documents.
- **Grep returned 16 lines but missed line 123** — [OBSERVED] session 019f9bfe transcript: the grep command and its 16-line output are in the turn where I wrote the false gap claim. The operator's pushback ("I thought we had updated the close orchestration") is what surfaced the miss.
- **The three instances in session 019f9bfe** — [OBSERVED] session transcript: (1) crawl4ai upgrade recommendation without grepping `web-scraping-tool-alternatives-free-tier.md`, (2) `/tp quick` recommendation without reading `/tp/SKILL.md` mode definitions, (3) `/close`-`/aar` false gap without grepping for "aar" or "retrospective."
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - session-019f96f5 (the incident — close-scanner-verification-gap-stale-read concept)
  - C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py:422-510 (the source read after pushback)
  - C:\Users\brsth\.grok\AGENTS.md "Claims require receipts" rule
relations:
  - target: wiki/concepts/plausible-narratives-substitute-for-verification.md
    type: refines — adds the causal-mechanism + durable-write surface form
  - target: wiki/concepts/go-home-narrative-fabricated-session-state-constraints.md
    type: related — sibling in the closure-pressure family; that concept covers anthropomorphic stop-narratives, this covers unreceived causal mechanisms. Both substitute feeling/narrative for receipt/measurement.
  - target: wiki/concepts/close-scanner-verification-gap-stale-read.md
    type: documented-by — that concept's correction incident is the worked example here
  - target: wiki/concepts/fabricated-causal-chain-receipt-required.md
    type: related — same failure class (causal claim without receipt)
---

# Causal mechanism claims require source inspection before durable write

## Decision context

**Why this concept was needed:** the `~/.grok/AGENTS.md` "Claims require receipts" rule is general — it forbids presenting inference as fact across all claim types. But the rule is enforced irregularly because the failure surface is broad. This concept names a specific high-risk surface form where the rule consistently fails: **causal mechanism claims written into durable artifacts.**

The trigger is narrow but the cost is high: a wrong causal mechanism in a wiki concept misleads every future session that reads it. The fix is narrow too: read the source before writing, not after the operator asks "explain clearly."

## The high-risk surface form

Three conditions together raise the risk that an inferred causal claim ships as fact:

1. **The claim is a causal mechanism** — "X happens because <how the system works internally>"
2. **The artifact is durable** — wiki concept, handoff, ADR, commit message, skill doc
3. **The agent has observed the behavior but not read the source** — inference from input/output, not from code

When all three are true, the agent has a plausible narrative (the behavior was observed) and a closure-pressure incentive (the artifact is being written now). The combination reliably produces inference-as-fact.

## The falsifier question

The operator's "explain clearly" / "what's your evidence" / "show me the receipt" is the canonical test. If the agent's honest answer would require reading the source for the first time, the original claim was inference presented as fact. The question is not hostile — it is the structural test the rule needs.

## Worked example — the incident that surfaced this rule (2026-07-25)

**Setup:** session 019f96f5 ran `/check` (6 verifiers PASS) then `/close`. The close scanner reported `VERIFICATION_GAP` despite the verifiers. The operator asked me to "explain clearly."

**The inferred mechanism (shipped without source inspection):**
> "The scanner can't see /check subagent transcripts because it greps only the parent transcript."

**The actual mechanism (after reading `close_accounting.py` for the first time):**
- Lines 422-510: `_scan_implicit_verification()` reads only `chat_history.jsonl` for the session. ✅ Mechanism claim survived.
- Lines 404-414: detect patterns are `pytest`, `python -m pytest`, `python verify_*.py`. ✅ Mechanism survived.
- The wiki concept also claimed "verifiers DID run tests." ❌ This collapsed — verifiers ran git/static checks, no pytest.

**The recovery:** the wiki concept was patched to separate the verified mechanism (scanner can't see subagent transcripts — true) from the overclaim (verifiers ran tests — false). The mechanism half survived because the inference happened to be correct; the overclaim half collapsed because no receipt existed.

**The lesson:** I got lucky on the mechanism half. The inference-from-behavior method produced a correct claim there and a wrong claim in the same concept elsewhere. There is no way to know which half is which without reading the source.

## Why inference-from-behavior feels sufficient (and isn't)

When you observe "scanner reports gap despite /check running," the inference "scanner can't see /check" feels tight — it's the simplest explanation. But "feels tight" is the same signal as "plausible narrative sufficiency," which is the failure mode the receipt rule exists to prevent. The inference has no receipt; it has a feeling.

The receipt is: `close_accounting.py:422` opens `chat_history.jsonl` only. That's a receipt. Without having read it, the claim is `[INFERENCE]`, not `[FACT]` — regardless of how tight the inference feels.

## The rule

**Before writing "X happens because <mechanism>" into a durable artifact:**
1. **Stop.** Recognize the trigger (causal mechanism + durable write).
2. **Read the source.** Open the file that implements the mechanism. Find the lines that do what you're about to claim.
3. **Cite the receipt.** In the artifact, reference the source location (file:lines or function name). If you can't cite line numbers, you don't have the receipt.
4. **Label appropriately.** If the source confirms the claim, ship as `[FACT] — receipt: <file:lines>`. If the source is unavailable, ship as `[INFERENCE]` and say what would verify it.

## Why "after operator pushback" is too late

The pushback-then-read pattern (what this session did) is better than never reading the source, but it has three costs:

1. **The wrong version shipped first.** A future session reading the wiki concept between write and correction would have taken the overclaim as fact.
2. **The correction is visible.** The wiki concept now has a "Honest caveat" block that was forced by operator pushback — a signal to future readers that the original author wasn't sure.
3. **Operator cognitive load.** The operator had to ask "explain clearly." That's exactly the meta-action the "automate user meta-actions" rule says should be eliminated.

The fix moves the source-reading BEFORE the write, eliminating all three costs.

## How to spot the trigger in your own output

Before finishing a wiki concept, handoff, ADR, or commit message, scan for:

- "X happens because..."
- "The system works by..."
- "The mechanism is..."
- "X can't see Y because..."
- "The scanner/gate/hook does X..."

Each is a causal mechanism claim. For each, ask: "Have I read the source that implements this mechanism in this session?" If no, read it before shipping.

## Related to existing rules

This refines (does not replace):

- **"Claims require receipts"** (`~/.grok/AGENTS.md`) — applies to all claims; this concept names the specific surface form where the rule most often fails
- **"Narrative-as-signal"** (`P:/AGENTS.md`) — "the moment you think 'this can't be done because X,' check whether you've read the documentation" — same pattern, generalized
- **"Plausible narratives substitute for verification"** (wiki) — the parent failure class; this concept is the durable-write-specific instance

## Falsifier

This concept is wrong if:
- **Source inspection before durable writes consistently finds the inference was correct** — in that case the rule is overhead; just ship the inference. (Unlikely: the worked example had a 50% collapse rate.)
- **Operators stop asking "explain clearly" because claims are reliably sourced** — in that case the rule is working and becomes self-reinforcing.
- **A future session reads this concept and still ships an unreceived causal mechanism** — the rule needs structural enforcement (a hook that greps wiki concepts for "because" / "mechanism" and demands a `receipt:` field). Not currently implementable reliably; treat as behavioral.

## Cold-start protocol

If you are about to write a wiki concept, handoff, or commit message and you find yourself writing "because <mechanism>":

1. Stop.
2. Open the source file that implements the mechanism.
3. Find the lines.
4. Cite them in the artifact.
5. If you can't find them, the claim is `[INFERENCE]`, not `[FACT]`.

The operator should not have to ask "explain clearly." The receipt should already be in the artifact.

## Related concepts

- [[plausible-narratives-substitute-for-verification]] — the parent failure class
- [[fabricated-causal-chain-receipt-required]] — same failure class, different surface
- [[close-scanner-verification-gap-stale-read]] — the worked example (corrected version)
