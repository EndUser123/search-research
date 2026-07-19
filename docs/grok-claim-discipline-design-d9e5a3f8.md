# Grok Claim-Discipline Design (d9e5a3f8)

**Problem class:** Recurring LLM failure modes — premature search termination, evidence confabulation, defensive hedging — that the rules in this workspace already cover but do not reliably fire.

**Scope:** This design covers the **Grok Build** host (the user's current runtime) and the **Claude Code** host (where the existing `StopHook_cross_validator.py` lives). It is **not** Cursor or Codex — they share the Grok hook surface but have not been audited for this failure class. Do not promote findings into Cursor/Codex without their own calibration pass.

**Status:** Design. No implementation has started. Every gate proposed here is **advisory until `measured_tp_on_corpus` shows ≥28/30 TP and ≤2/30 FP on a real held-out corpus** (workspace rule, `P:\.claude\CLAUDE.md` v9.0).

**Host-scope flag (added 2026-07-18, post-review):** This design spans two hosts, but **the user runs Grok Build.** PRs 5–8 extend `StopHook_cross_validator.py` under `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/` — a **Claude Code** hook that does NOT fire in Grok Build sessions (verified: `P:/.data/wiki/concepts/grok-build-hook-host-ceiling.md`). In Grok Build, the design reduces to PRs 2–4: `/tp` vocabulary + two passive `systemMessage` banners, neither of which blocks. There is no structural lever in Grok Build that prevents failure modes #1/#2 from shipping in the turn they happen. Path-forward decision required from the user: (A) accept the Grok ceiling and prune PRs 5–8; (B) keep PRs 5–8 but mark Claude-Code-only and run claim-discipline-sensitive sessions in Claude Code; (C) design a Grok-side `PreToolUse` upstream-verification gate (different design, not yet scoped). See `P:/.data/wiki/concepts/grok-build-hook-host-ceiling.md` for the verified mechanics.

**SOURCE-CORRUPTION FLAG (RESOLVED 2026-07-18):** Sections §1.3, §4.3, §6.3, §9, and §11 Decision 5 addendum previously cited `marketplace-cache/b975999a270027c6/src/cli/types.ts` as "Grok runner source." That was wrong — `b975999a270027c6` is `thedotmack/claude-mem` v13.11.0, a third-party plugin. See `P:/.data/wiki/concepts/grok-marketplace-cache-is-third-party-not-host` and `P:/.data/wiki/concepts/source-authority-confabulation-from-cache-dirs`. A runtime probe confirmed: **passive-event stdout does NOT reach the model in Grok Build** (622 firings, 4 channels, 0 tokens across 77 session transcripts). The doc's "stdout is ignored for passive events" is a complete statement. **PRs 3 and 4 are non-functional in Grok Build. Prune them.** The design collapses to Option A: `/tp` vocabulary (PR 2) + rules (PR 10) + Claude-Code-only blocking (PRs 5–8, don't fire here). There is no structural lever in Grok Build that prevents failure modes #1/#2 from shipping in the turn they happen.

**Multi-terminal isolation compliance (added 2026-07-18):** This design complies with the workspace's multi-terminal isolation invariant (`P:/.data/wiki/concepts/multi-terminal-isolation-invariant.md`). PRs 3 and 4 are stateless (return `HookResult`, no file writes). PR 6's corpus analysis is read-only against `~/.grok/memtrace/`, `~/.grok/sessions/`, and `~/.claude/hooks/.evidence/` — no cross-terminal mutable state is created. PR 5–8 extensions to `StopHook_cross_validator.py` inherit the existing hook's state-file conventions (already namespaced per `P:/.claude/rules/file-operations.md` "Instance Isolation"). No `LATEST-*` pointers, no timestamp discovery, no cross-terminal scanning. If a future PR introduces mutable state, it must follow the `{terminal_id}_{session_id}` naming rule.

---

## 1. Problem reframe (binding)

### 1.1 The user's stated problem

Three failure modes happened in a prior session:

| # | Failure mode | Observable signal |
|---|---|---|
| 1 | **Premature search termination** | One web search performed; web result already contained the answer (CWD default for `/export`); assistant said "I cannot tell you from documentation alone." |
| 2 | **Evidence confabulation** | `.md` files in `C:\Users\brsth\Downloads` were cited as proof of the tool's `/export` behavior. Those were user-authored transcripts from multiple tools, not tool outputs. |
| 3 | **Defensive hedging under challenge** | When the user replied "FALSE!!! Your 'direct evidence' nonsense are files that I CREATED," the assistant walked back with "What I can verify / What I cannot verify" framing instead of conceding in sentence one. |

### 1.2 Why this is **not** a missing-rules problem

All three failure modes are already named in the workspace's binding context:

| Failure mode | Existing rule that names it | Source |
|---|---|---|
| #1 Premature search termination | "Look Up First", "Absence Conclusions" | `P:\.claude\CLAUDE.md` v9.0 + `~/.grok/AGENTS.md` |
| #2 Evidence confabulation | "Trust over believability", "Provenance", "Attribution Claims" | `~/.grok/AGENTS.md` + `P:\.claude\rules\provenance.md` |
| #3 Defensive hedging | "Truthfulness > agreement", "thought partner first" | `P:\.claude\CLAUDE.md` v9.0 + `~/.grok/AGENTS.md` |

The failure was **rule non-firing**, not rule absence. Rules sitting in context are text; they do not reliably trigger at the moment of drift. A design whose primary recommendation is "add three more AGENTS.md rules" is **cargo-cult** — explicitly forbidden by the binding reframe. Rules are the lowest-leverage lever for this problem; they are kept in this design only as a secondary reinforcement, never as the primary mechanism.

### 1.3 The host ceiling we cannot engineer around

**Verified by direct read of `~/.grok/docs/user-guide/10-hooks.md` line 99:**

> *"Only `PreToolUse` can block a tool call; every other event is passive."*

All three failure modes manifest in the assistant's *response text*, which is emitted **after** all tool calls complete. There is no Grok `PreToolUse` event for "the assistant is about to submit its final message" because ending a turn is not a tool call. Therefore:

- Response-text failure modes **cannot be directly blocked** by any Grok hook.
- The same ceiling is documented in `P:\.data\wiki\concepts\llm-overconfidence-and-structural-assessment-failures.md`: *"Warn mode injects into the NEXT turn, but bad output already shipped."*

This design must not pretend otherwise. The available structural levers in Grok are:

| Lever | What it can do | What it cannot do | Source / confidence |
|---|---|---|---|
| **Grok `PreToolUse` upstream-verification gate** | Deny a tool call until a prior verification tool has run in the turn (e.g., require `web_search` before any `web_fetch` return can be cited) | Inspect the eventual claim text | Doc (`~/.grok/docs/user-guide/10-hooks.md:99`) — only `PreToolUse` blocks. High confidence for the blocking fact; the *upstream-verification* shape is a design choice, not yet implemented. |
| **Grok `Stop` passive injection — `USER_HINT` channel** | Hook returns `HookResult.systemMessage`; runner surfaces to the human via the platform adapter. May or may not be surfaced inline to the model depending on platform. | Block the current turn's bad output | Source: `marketplace-cache/b975999a270027c6/src/cli/types.ts:21-34` (HookResult has `systemMessage` field, event-agnostic), `shared/hook-io.ts:6-16` (USER_HINT intent vocabulary). **Confidence: low/undemonstrated for `Stop` specifically — no `stop.ts` handler in `src/cli/handlers/` (8 files, verified by `list_dir`). `HookResult` is type-permitted but no in-tree handler exercises the channel end-to-end for `Stop`.** |
| **Grok `Stop` passive injection — `MODEL_CONTEXT` channel** | Hook returns `HookResult.hookSpecificOutput.additionalContext`; runner emits via `emitModelContext(adapter, result)` (`hook-io.ts:113-127`) and JSON-stringifies through `adapter.formatOutput`. Model-consumed directly. | Block the current turn's bad output | Same source citations as above. **Confidence: low/undemonstrated for `Stop` — same gap.** `additionalContext` is demonstrated for `SessionStart` only (`handlers/session-init.ts:169-172`). |
| **Grok `UserPromptSubmit` passive injection — `USER_HINT` channel** | Hook returns `HookResult.systemMessage`. Demonstrated end-to-end: `handlers/user-message.ts:42` returns `{ exitCode: HOOK_EXIT_CODES.SUCCESS, systemMessage: bannerText }`. | Block the current turn's bad output | **Confidence: high for human-visible delivery; medium-low for model-consumption** (platform-dependent surfacing). |
| **Grok `UserPromptSubmit` passive injection — `MODEL_CONTEXT` channel** | Hook returns `HookResult.hookSpecificOutput.additionalContext`. **Not demonstrated in-tree for UserPromptSubmit** — `user-message.ts:42` returns `systemMessage` only, not `additionalContext`. | Block the current turn's bad output | **Confidence: medium-low** — type-permitted by HookResult, propagation confirmed at `adapters/claude-code.ts:28-42`, but no in-tree UserPromptSubmit handler exercises `additionalContext` end-to-end. |
| **Claude-Code `StopHook_cross_validator.py`** (already exists) | Block at Claude Code's Stop event with mode=block | Fire only inside Claude Code sessions, not Grok Build | Source: `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/hooks/stop/StopHook_cross_validator.py:129-210`. High confidence (in-tree evidence: every cc-aca-epistemic Stop invocation). |
| **Skill vocabulary extension** (extend `/tp`) | Give the model a named drift mode so a human-invoked `/tp <name>` can diagnose it later | Auto-fire; must be invoked by the user or a calling agent | Source: `C:/Users/brsth/.grok/skills/tp/SKILL.md`. High confidence for the existing surface; the extension is a content edit only. |
| **Subagent/agent-class detector** | Spawn a reviewer that scores the prior turn against the failure-mode catalog | Run synchronously inside the assistant's turn without latency cost | No in-tree evidence. Speculative. |
| **Durable-artifact checklist** | Force a written pre-flight (FACT/INFERENCE/UNKNOWN) for material claims | Prevent a bad turn; only audit the next one | Source: `P:/.claude/rules/epistemic-format.md`. High confidence for the rule; the gate-level enforcement is a design choice, not yet implemented. |

Every lever here is honest about its ceiling. None of them claim to block the bad turn in Grok Build.

**Citation discipline note (binding):** the user-guide doc's line "Only `PreToolUse` can block a tool call; every other event is passive" (`~/.grok/docs/user-guide/10-hooks.md:99`) and the related "stdout is ignored for passive events" line (`:204`) are correct about the **allow/deny decision path** — they are NOT a statement that passive hooks cannot surface content via `HookResult.systemMessage` or `hookSpecificOutput.additionalContext`. The hook doc is the source of truth for the blocking fact; the runner source (`marketplace-cache/b975999a270027c6/src/cli/types.ts` et al.) is the source of truth for the surfacing mechanism. Conflating the two was a first-round error and is corrected throughout this design.

---

## 2. Trigger conditions (what fires right before each bad turn)

A rule that does not name its trigger does not fire. For each failure mode, the trigger is the observable signal in the assistant's turn (or just before it) that, if present, would have predicted the bad output.

### 2.1 Trigger for #1 — Premature search termination

**Cheap structural signal:** response text matches an **ignorance-claim pattern** AND no verification tool was called in the turn.

Ignorance-claim patterns (regex, illustrative; not final):

```regex
(?i)\b(I\s+(can(?:not|'t)|cannot)\s+(tell|say|determine|verify|confirm|find))\b[^\.]{0,80}\b(from|by|in)\s+(the\s+)?(docs?|documentation|read[-_ ]?me|alone|context\s+I\s+have)\b
(?i)\b(not\s+in\s+(the\s+)?(context|docs?|documentation))\b
(?i)\b(cannot\s+be\s+(determined|verified)\s+from\s+(the\s+)?(docs?|documentation|alone))\b
```

Verification tools that count as "search was attempted": `read_file`, `grep`, `list_dir`, `web_search`, `web_fetch`, `run_terminal_command` with read-like commands. Tool-name aliases per Grok's mapping (`Read`→`read_file`, `Bash`→`run_terminal_command`, etc.).

**Detection cost:** low — regex on response + tool-event log lookup.

**Falsifier for the trigger itself:** the regex catches a legitimate, well-evidenced ignorance claim ("I cannot tell from the docs alone because the docs are version 1.2 and the question is about 1.4 — let me check release notes"). Counter-signal: prior `web_fetch`/`web_search` in the turn whose result returned no usable information. Falsifiability of the trigger is why a held-out corpus is required before any gate ships.

### 2.2 Trigger for #2 — Evidence confabulation

**Cheap structural signal:** response text matches a **document/source claim pattern** AND no `Read`/`read_file`/equivalent call to the named artifact happened in the turn AND no provenance marker (timestamp, hash, citation URL) accompanies the claim.

Document-claim patterns (from `StopHook_cross_validator.py::has_document_claim`, illustrative):

```regex
(?i)\bthe\s+(document|file|log|transcript|export|output)\s+(says|states|contains|shows|confirms|has|returns)\b
(?i)\baccording\s+to\s+(the\s+)?(file|document|log|readme|docs?)\b
(?i)\bI\s+(read|saw|found)\s+(in|from)\s+(the\s+)?(file|document|log|readme)\b
(?i)\bin\s+the\s+(file|document|log|readme),\s+(it|there|this)\b
```

**Distinguishing fabrication from meta-discussion:** this is the gap that already burned us once (Task #1123 in `StopHook_cross_validator`). The detector must distinguish first-person ("I read in the file that…") from third-person ("the answer was in the file it just made"). Three viable shapes, all requiring held-out corpus validation before shipping (see §5):

- **A. Framing-aware trigger** — first-person pattern only, OR third-person patterns gated on negative signal (`it searched`, `the pasted LLM`, `the transcript shows`, `the other model`, `it concluded` within N chars).
- **B. Prompt-context plumbing** — give the detector access to the user prompt so it can detect "the assistant is analyzing pasted content" and stand down. Requires plumbing at the dispatch boundary.
- **C. Citation-shape restriction** — third-person patterns must be followed by a quoted span, file path with extension, or URL.

**Parallel-line comparison (A vs C — the two viable single-regex paths):**

| Axis | Path A (framing-aware) | Path C (citation-shape) |
|---|---|---|
| Plumbing cost | Low — one additional regex pass | Low — same |
| TP rate (estimate; corpus-gated) | High on first-person fabrication | High on explicit citation; low on paraphrase |
| FP rate (estimate; corpus-gated) | Medium — meta-discussion may slip through | High — legitimate paraphrased analysis looks like fabrication |
| Maintenance | Negative-signal list drifts over time | Citation-shape list must be curated |
| Reversibility | Easy to remove the negative-signal window | Easy to relax to Path A |
| Failure-shape coverage | First-person fabrication + meta-discussion-with-cue | Only "explicit citation without Read" |

Path **A** is the recommended default (lowest plumbing cost; smallest blast radius). Path **B** is the most general but requires the largest plumbing change (dispatch boundary). Path **C** is the strictest and has the highest FP risk on legitimate paraphrased analysis — it is a fallback if Path A's held-out TP drops below the 28/30 floor; it is not the first choice.

**Detection cost:** low — regex on response + tool-event log lookup. The framing-aware variant adds one more regex pass.

### 2.3 Trigger for #3 — Defensive hedging under challenge

**Expensive semantic signal — flagged as "type: agent territory" by the existing wiki.**

From `P:\.data\wiki\concepts\llm-overconfidence-and-structural-assessment-failures.md`, verbatim:

> *"Detecting defensive pivots ('you're right BUT' followed by continued defense) requires turn history tracking and rhetorical stance analysis. This is type: agent territory — pattern matching cannot reliably detect rhetorical pivots across turns."*

Possible cheap proxy signals (each has a known false-positive class):

| Proxy signal | FP class |
|---|---|
| Response opens with "You're right" or "Fair point" + continues defending | Genuine update with new evidence |
| Response uses "What I can verify / What I cannot verify" enumeration after a user challenge | Honest scoping when the user really did overclaim |
| Response uses "I see your point, but…" | Legitimate steelman-then-pivot |
| Response opens with hedging ("Let me reconsider", "On reflection") but does not actually reverse the prior claim | Pure hedging without reversal |
| Response rewrites the prior turn's framing without acknowledging the user's correction | Silent reframe, often worse than #3 |

**There is no cheap regex for #3.** A pattern-matching detector will either over-fire (catching legitimate updates) or under-fire (missing sophisticated defense). The wiki verdict is correct, and this design accepts it: #3 is **not** a hook-gate candidate.

---

## 3. Lever selection per failure mode

Each lever is enumerated with its host, blocking capability, and the trigger it gates on. **Blocking gates are advisory until measured.**

### 3.1 Failure mode #1 — Premature search termination

| Lever | Host | Blocks? | Trigger gated | Justification |
|---|---|---|---|---|
| **(i) Trigger-named rule rewrite** | Grok + Claude | No | Ignorance-claim pattern + no tool call in turn | Lowest blast radius; cheap to ship; reinforces existing rules |
| **(ii) User-invoked skill gate (extend `/tp`)** | Grok + Claude | No | Drift name "premature-termination" added to vocabulary | Reuses existing invocation surface; no new plumbing |
| **(v) Claude-Code `StopHook_cross_validator.py` extension** | Claude Code only | **Yes** (mode=block) | Ignorance-claim + no verification tool in turn | Already-deployed blocking infrastructure |
| **(iv) Grok `Stop` passive injection** | Grok | No (warn) | Ignorance-claim pattern at Stop | Reactive; bad output already shipped; nudges next turn |

**Chosen primary lever:** **(v) Claude-Code `StopHook_cross_validator` extension + (iv) Grok `Stop` passive injection.** Reasoning: only `StopHook_cross_validator` actually blocks, and it already has the tool-event log lookup we need for the "did verification happen" check. The Grok `Stop` injection is the only structural lever available on the Grok side — it cannot block, but it gives the model a counter-signal at the next turn start. The skill vocabulary extension (ii) covers the human-invoked diagnostic case.

**Selected alternative rejected:** A new Grok `PreToolUse` gate that denies all tools after an ignorance claim. **Rejected because:** ignorance claims happen in the response text, not in tool calls — the gate would fire after the fact, and there is no tool call to deny at that point. The upstream-verification force (require `web_search` before any subsequent tool) is theoretically possible but adds latency to every turn and is unjustified by a single failure-mode example.

### 3.2 Failure mode #2 — Evidence confabulation

| Lever | Host | Blocks? | Trigger gated | Justification |
|---|---|---|---|---|
| **(v) Claude-Code `StopHook_cross_validator.py::verify_document_claim` (already exists)** | Claude Code only | **Yes** (mode=block) | Document-claim pattern + no Read tool | Already deployed; needs framing-aware fix per §5 |
| **(vi) Grok `Stop` passive injection** | Grok | No (warn) | Document-claim pattern + no Read tool | Reactive injection; nudges next turn |
| **(vii) Durable-artifact checklist** | Both | No | Material claim detected | Forces the model to write `[FACT]/[INFERENCE]/[UNKNOWN]` per `epistemic-format.md` |

**Chosen primary lever:** **(v) Fix the existing `StopHook_cross_validator.py::verify_document_claim` at detector scope** (Path A: framing-aware trigger), with **(vi) Grok `Stop` passive injection** as the Grok-side counterpart and **(vii) durable-artifact checklist** as the deeper-substance reinforcement.

**Selected alternatives rejected:**
- **(i) Trigger-named rule rewrite only** — already tried in spirit (the rule exists); rule non-firing is exactly why this design is needed.
- **(iii) Subagent reviewer that scores the prior turn** — high latency, single-gate, and the cheap regex already catches the cheap case; subagent is overkill for the cheap case and unreliable for the sophisticated case.

### 3.3 Failure mode #3 — Defensive hedging

**This mode gets a different lever than #1/#2 and here is why.**

Per the existing wiki, #3 is **type: agent territory** — pattern matching cannot reliably detect rhetorical pivots across turns. The cheap signals exist but have high false-positive rates against legitimate updates, steelmen, and honest scoping. A blocking gate that over-fires on #3 would be **catastrophic** (see §6 — over-firing pushes the model toward confident fabrication).

| Lever | Host | Blocks? | Trigger gated | Justification |
|---|---|---|---|---|
| **(ii) User-invoked skill gate (extend `/tp` with new drift mode)** | Grok + Claude | No | New mode "defensive-hedging" added to `/tp` vocabulary | Reuses existing skill surface; lets the user invoke `/tp` after the fact |
| **(iii) Subagent/agent-class detector** | Both | No | Drift name + cross-turn history | The only lever that can actually detect rhetorical pivots; latency cost acknowledged |
| **(iv) Grok `UserPromptSubmit` passive injection** | Grok | No (warn) | Last turn's user message included a corrective challenge ("FALSE", "wrong", "you're not addressing") | Reactive; can pre-load context for next turn |
| **(vii) Durable-artifact checklist** | Both | No | User-challenge detected | Force a one-line concession if the user's challenge is correct |

**Chosen primary lever:** **(ii) Extend `/tp` with a new drift mode `defensive-hedging`** + **(iv) Grok `UserPromptSubmit` passive injection** keyed on corrective-challenge signals + **(iii) optional subagent review** for high-stakes turns.

**Selected alternative rejected:** **(v) blocking gate based on "you're right BUT" regex.** Rejected because the FP rate is unacceptable — legitimate steelman updates look identical to defensive pivots. A blocking gate that over-fires on this signal would push the assistant into agreeing with every user correction, which is the **opposite** of thought-partner stance and would amplify agreeableness bias (which is mode #1 in `/tp`).

**Reconciliation with §2.3 verdict:** the cheap proxy signals in §2.3 are usable **for the passive nudge (PR 4)** because a passive nudge can tolerate the FP risk — it surfaces an advisory that the model may act on or ignore, and the worst case is a redundant reminder. The §2.3 verdict ("no cheap regex for #3") applies to **blocking variants**. PR 4 deliberately chooses the lower-impact channel precisely so that the FP-tolerant signals become acceptable.

---

## 4. Reuse / extension plan

### 4.1 Extend `/tp` (C:\Users\brsth\.grok\skills\tp\SKILL.md)

The `/tp` skill currently exposes 6 drift modes. Adding three new modes preserves its existing argument-routing (`/tp <mode>`) and the five-line circuit breaker. No new plumbing.

Proposed additions to the `/tp` vocabulary table:

| # | Mode | Symptom in last turn | Correction |
|---|---|---|---|
| 7 | **Premature termination** | Ignorance claim after sparse search, when one more tool call would have answered it | Force one more verification step before answering. Read the source. Do the search. Do not emit "I cannot tell" until at least two distinct verification attempts. |
| 8 | **Evidence confabulation** | Cited a file/doc/log/URL as proof without a Read tool call to that artifact in the turn | Drop the citation. Say "I have not read that file yet." Then read it, or state `[INFERENCE]`/`[UNKNOWN]` explicitly. |
| 9 | **Defensive hedging** | "What I can verify / What I cannot verify" structure after a user challenge, or "you're right BUT" pivots that defend rather than update | First sentence concedes if the user is right. If they are wrong, name the falsifier — do not enumerate scopes. Reviewers return findings; they don't rewrite charters. |

Mode 9 is the new mode that addresses the user's third failure mode. Mode 8 is the new mode for confabulation. Mode 7 is the new mode for premature termination.

The existing Falsifier clause in `SKILL.md` (`If the user invokes /tp after real drift and the skill produces a generic "I'll try harder" response...`) extends naturally to modes 7–9: a generic "I'll search more carefully" without naming the specific failure mode from the prior turn is mode 6 (performative rigor) and must itself be called out.

**Important constraint:** `/tp` is user-invoked, not auto-fired. The skill explicitly states: *"Not a hook. Does not auto-fire. The user notices drift and invokes it. Auto-firing would make it noise."* Extending `/tp` does **not** solve rule non-firing on its own; it gives the user a sharper instrument after the fact and gives the model a named drift to diagnose if a `/tp` invocation happens. The structural lever (the Claude-Code Stop hook + the Grok Stop injection) is what prevents the next occurrence.

### 4.2 Extend `StopHook_cross_validator.py::verify_document_claim`

This is the closest published analogue. It already exists at `P:\packages\.claude-marketplace\plugins\cc-aca-epistemic\hooks\stop\StopHook_cross_validator.py:129-210`. Verified by direct read. Two extensions:

1. **Add an ignorance-claim detector** alongside the existing document-claim detector. Same tool-event lookup; same block-on-match logic. The trigger regex from §2.1.
2. **Fix the framing-aware trigger** per `P:\.data\wiki\concepts\confabulated-ignorance-and-source-fabrication-gate.md` Path A. Either split first-person from third-person patterns, or add a negative-signal window for third-person meta-discussion markers (`it searched`, `the pasted LLM`, `the other model`, `the transcript shows`, `it concluded` within N chars).

Both extensions are **gate-weakening** changes (the framing fix can drop TP on real-world inputs). Per workspace rule, neither ships without `measured_tp_on_corpus` ≥28/30 TP AND ≤2/30 FP on a real held-out corpus. See §5 for the corpus plan.

### 4.3 New Grok `Stop` and `UserPromptSubmit` passive injection hooks

Two new global hooks at `~/.grok/hooks/`. The mechanism is **not** "writes a session-scoped file that the next session-start reads" (that is the Claude-Code state-file pattern; it is not how Grok's hook contract works). The actual mechanism is:

> The hook returns a `HookResult` containing `systemMessage` (USER_HINT) and/or `hookSpecificOutput.additionalContext` (MODEL_CONTEXT). The runner propagates both via `emitModelContext(adapter, result)` (`shared/hook-io.ts:113-127`) and the platform adapter's `formatOutput` (`adapters/claude-code.ts:28-42`). Both fields are **event-agnostic** on `HookResult` (`cli/types.ts:21-34`), so the same shape works for any event the runner routes — including `Stop` and `UserPromptSubmit`.

**Channel choice** (deliberate, justified per PR):

| Channel | Field | Precedent in-tree | Confidence |
|---|---|---|---|
| `USER_HINT` | `HookResult.systemMessage` | `handlers/user-message.ts:42` (UserPromptSubmit) | **High** for human-visible delivery |
| `MODEL_CONTEXT` | `HookResult.hookSpecificOutput.additionalContext` | `handlers/session-init.ts:169-172` (SessionStart only) | **Medium-low** for events other than SessionStart |

#### PR 3 — `claim-discipline-stop-warn` (Grok `Stop`, USER_HINT)

- **Event:** `Stop`.
- **Channel:** `USER_HINT` via `HookResult.systemMessage`. Chosen over `MODEL_CONTEXT` because: (a) it matches the only in-tree demonstrated channel for surfacing text from a passive hook (`user-message.ts:42`); (b) `Stop` is undemonstrated end-to-end in-tree (see precision note below), so picking the lower-blast-radius channel is the right default; (c) surfacing to the human is the correct audience for a "last turn may have been bad, please review" advisory.
- **Payload:** the hook returns `{ systemMessage: "Last turn matched the premature-termination or evidence-confabulation trigger. Verify sources before citing in the next turn." }`.
- **Mechanism caveat:** the hook returns this `HookResult` via stdout JSON; the runner routes it via the platform adapter; the claude-code adapter's `formatOutput` (`adapters/claude-code.ts:28-42`) propagates `systemMessage` with no event-type gating.

**Precision note (binding):** the `Stop` event is **type-permitted by `HookResult`** (verified at `cli/types.ts:21-34` — the interface is event-agnostic), but **undemonstrated end-to-end** in the marketplace-cache plugin source. Verification: `list_dir` of `C:/Users/brsth/.grok/marketplace-cache/b975999a270027c6/src/cli/handlers/` returns 8 files (`context.ts`, `file-context.ts`, `file-edit.ts`, `index.ts`, `observation.ts`, `session-init.ts`, `summarize.ts`, `user-message.ts`) — **no `stop.ts` handler**. Therefore:

- **No in-tree code path demonstrates that a hook returning `HookResult` on a `Stop` event actually surfaces via the platform adapter.** The mechanism is real per the contract, but the in-tree handler set does not exercise it.
- **Confidence:** Low / undemonstrated for `Stop` specifically. **High** for `SessionStart` (via `session-init.ts`) and `UserPromptSubmit` (via `user-message.ts`).
- **PR 3 mitigation:** the hook MUST be treated as best-effort pending post-deployment measurement per §5/§7. Falsifier **F4** (Grok `Stop` injection ignored) becomes the dominant falsifier for PR 3. If F4 fires, replace the lever with `UserPromptSubmit`-only (which IS demonstrated) per §7.

#### PR 4 — `corrective-challenge-injection` (Grok `UserPromptSubmit`, USER_HINT)

- **Event:** `UserPromptSubmit`.
- **Channel:** `USER_HINT` via `HookResult.systemMessage`. Chosen because: (a) it is the only channel demonstrated end-to-end for this specific event (`handlers/user-message.ts:42`); (b) the payload is an advisory about how to approach the next turn, not model-bound context that the user must not see.
- **Payload:** the hook scans the user's message for corrective-challenge signals (`FALSE`, `wrong`, `you're not addressing`, `no that's not what I said`) and, on match, returns `{ systemMessage: "User issued a corrective challenge. Consider whether drift occurred before responding." }`. **Neutral text — does NOT auto-suggest `/tp`** (see Issue 7 / Decision 7 alignment).
- **Mechanism:** same as PR 3 — hook returns `HookResult` via stdout JSON; runner routes via platform adapter.

**Both hooks are passive.** The doc line *"Only `PreToolUse` can block a tool call; every other event is passive"* (`~/.grok/docs/user-guide/10-hooks.md:99`) is the source of truth for the blocking fact. The runner source (`marketplace-cache/b975999a270027c6/src/cli/types.ts` et al.) is the source of truth for the surfacing mechanism. They are not in conflict; they describe different facts.

**Both hooks cannot prevent the bad turn; they only surface content to the audience their channel targets.** Their value is **cumulative** — over many sessions, the surfacing becomes part of the model's habitual input. They are also text-shaped levers (see §11 Decision 1 augmentation); they inherit the same limited-effectiveness profile the workspace found in 2025 when it shifted from text injection to blocking hooks (`P:/.data/wiki/concepts/hook-architecture.md:27` — "v2 (2025): Shifted to blocking hooks after finding injection easily ignored"). They should be treated as a **low-cost hedge**, not as a high-confidence primary lever. The Claude Code `StopHook_cross_validator` extension (PRs 5–8) carries the primary load.

---

## 5. Measurement plan (`measured_tp_on_corpus`)

Per the workspace rule: *"Every new enforcement gate must ship with a `measured_tp_on_corpus` field (real held-out corpus TP/FP) before it can block; a gate that fires 0 real positives stays advisory."* No gate in this design blocks until measurement.

### 5.1 Corpus sources (named)

For Grok Build data:

| Source | Path | Format | Notes |
|---|---|---|---|
| **Grok session memtrace** | `C:/Users/brsth/.grok/memtrace/*.jsonl` | JSONL, ~50+ files | Holds turn-level tool-call and response events for Grok sessions |
| **Grok sessions dir** | `C:/Users/brsth/.grok/sessions/P%3A%5C/` | Mix of .json/.jsonl/.log | Larger; per-session transcript and tool event logs |
| **Grok unified log** | `C:/Users/brsth/.grok/logs/unified.jsonl` | JSONL | Single append-only event stream |

For Claude Code data:

| Source | Path | Format | Notes |
|---|---|---|---|
| **Claude Code hooks evidence** | `P:/.claude/hooks/.evidence/` | Per-hook evidence dirs | Verified per `P:\.claude\rules\file-operations.md` |
| **Claude Code errors log** | `P:/.claude/hooks/cc_errors.jsonl` | JSONL | Block/fail events |

For ground-truth labeling:

| Source | Notes |
|---|---|
| **The transcript of the user's prior bad session** | Already cited; the user's own pushback is the gold label |
| **Manually labeled prior sessions** | At least 30 sessions where the user pushed back on a claim — these are the positive class |

### 5.2 Measurement methodology

For each proposed gate:

1. **Authoring set (not the held-out set):** the `StopHook_cross_validator.py` test suite at `P:\packages\.claude-marketplace\plugins\cc-aca-epistemic\tests\` contains the regression baseline. The count of `def test_` methods across the cc-aca-epistemic tests directory is volatile — **205 across the whole `tests/` directory and 19 scoped to `test_quote_exemption_gates.py` alone as of 2026-07-18**. Both numbers must be re-verified at PR 6 write-time via the cited grep; the precise numbers will drift as the suite evolves. The wiki's "23 author-constructed cases" figure is stale and should not be cited verbatim. This is the regression baseline, **not** the held-out corpus.
2. **Pre-PR-6 sanity check (mandatory before corpus construction begins):** open two memtrace files and two session transcripts from §5.1 sources; verify that the per-turn response text can be **joined to the per-turn tool-call record** on a `(session_id, turn_index)` key; verify that user-pushback turns are **identifiable** by surface signal (presence of "FALSE", "wrong", "no that's not what I said", or similar in the user message of the next turn). If either join fails, the corpus cannot be labeled automatically and PR 6 cannot proceed without a different labeling strategy. This is a one-engineer-hour check, not a measurement run.
3. **Held-out set:** sample ≥30 turns from the user's prior Grok sessions where the user **did not** push back (negative class) and ≥30 turns where the user **did** push back (positive class). Label each turn as TP/FP/FN/TN against the new detector regex.
4. **Threshold:** ≥28/30 TP AND ≤2/30 FP, per workspace rule. If real-world TP drops below this floor after the framing-aware fix, the gate stays in **warn** mode (does not block).
5. **Time-boxed:** measurement run is bounded to one engineer-day. If the corpus cannot be labeled in that window, the corpus is too small or the labeling scheme is wrong — defer the gate until resolved.

### 5.3 Per-gate measurement state (initial)

| Gate | Status | Corpus | Threshold met? |
|---|---|---|---|
| `verify_document_claim` (existing, framing-fix proposed) | **Advisory — framing fix pending measurement** | Not measured | Unknown; baseline author-constructed test suite (`test_quote_exemption_gates.py` alone is 19; whole `tests/` directory is 205 as of 2026-07-18; both volatile per §5.2) is not held-out |
| New `verify_ignorance_claim` | **Advisory — not yet implemented** | Not measured | — |
| Grok `Stop` injection (PR 3, USER_HINT) | **Best-effort — passive; low/undemonstrated confidence per §4.3** | N/A — passive | N/A — treat as experimental; F4 is the dominant falsifier |
| Grok `UserPromptSubmit` injection (PR 4, USER_HINT) | **Warn (passive; demonstrated end-to-end via `user-message.ts:42`)** | N/A — passive | N/A |
| `/tp` vocabulary extension (modes 7–9) | **Advisory — skill vocabulary is reactive, not auto-fired** | N/A — diagnostic | N/A |

A passive `Stop`/`UserPromptSubmit` hook does not need a measured TP/FP because it cannot block — it is reactive text that the model may or may not act on. If measurement shows the model does not act on the injection, the lever is wrong and should be replaced, not strengthened. For `Stop` specifically (PR 3), low-confidence surfacing is the dominant risk: F4 (injection ignored) is more likely than F1 (over-fire).

---

## 6. Second-order risks ("could cause other problems")

Every lever has a failure mode of its own. Naming them is required because the most catastrophic possible outcome of a claim-discipline gate is **over-firing** that pushes the model toward confident fabrication over honest "I don't know yet."

### 6.1 The catastrophic risk (named separately because it is the worst)

**A claim-discipline gate that over-fires pushes the model toward confident false answers over honest "I don't know yet" — the exact opposite of the goal.**

Mechanism: if every "I cannot tell" gets blocked, the model learns to avoid "I cannot tell" and replaces it with **confident guesses** to satisfy the gate. That is the `false precision` failure mode (`/tp` mode #3) scaled up. It is worse than the original failure because it removes the model's last escape hatch — admitted uncertainty.

**Counter-measures (must all ship with the blocking gate):**

1. **Replace `I cannot tell` blocks with `I cannot tell AND I have not searched` blocks.** The trigger includes "no verification tool call in the turn." A model that has searched (read_file, web_search, grep) is allowed to say "I cannot tell" — the gate only fires on premature termination.
2. **Block message must be constructive.** The current `verify_document_claim` reason string is *"Document claim detected but no Read tool execution found... If you haven't read the document, say 'I haven't read that document yet.'"* — this is the right shape. A block that ends with `say "I don't know"` without telling the model what to do instead is a confident-fabrication factory.
3. **Keep a circuit breaker on the block frequency.** If a Stop hook blocks >X% of a session's turns, the gate auto-disables for the rest of the session and writes a notice to the user. This prevents a runaway loop where the model tries to answer, gets blocked, rewrites, gets blocked again, etc. (Throttling specifics are an implementation PR; the principle is non-negotiable.)
4. **Never block on `UserPromptSubmit`.** Only `Stop` (after the bad turn already shipped) or `PreToolUse` (on a tool call). User-visible blocking on submission is the worst UX.
5. **Periodic post-deployment re-measurement (PR 9 covers the first pass; a recurring cadence follows).** Once the model knows the trigger exists, it may begin to add a verify-before-cite hedge to every claim — prompt-shaped avoidance rather than substantive verification. This is mode 6 (performative rigor) *induced by the gate*. Counter-measure 1 (verification tool must run in the turn) catches the cheap shape (no Read happened); but a sophisticated model could add the hedge text without actually running a Read. To detect this, re-run a smaller held-out subset (e.g., 15–20 turns) every **~30 sessions** after PR 7 promotes to block. If FP rises (model gaming the trigger phrasing without verifying), soften the trigger or temporarily disable until the next re-measurement. Cadence and stop-condition are an implementation detail of the recurring measurement; the principle is non-negotiable.

### 6.2 Per-lever second-order risks

| Lever | Risk | Mitigation |
|---|---|---|
| Rule rewrite in AGENTS.md | Rule non-firing (the original problem) | Not the primary lever; structural hook is primary |
| `/tp` vocabulary extension | Skill drift into a recital (`/tp` becomes performance) | Existing Falsifier clause already catches this; extend it to cover modes 7–9 |
| Subagent review of every turn | Latency cost; agent bias | Only invoke on high-stakes turns (or after a user pushback); never synchronously in normal generation |
| Grok `Stop` passive injection | Model ignores the injection | Measurement on a held-out session set: did the model act on the injection? If 0 real positive influence, replace the lever |
| Grok `UserPromptSubmit` injection on corrective challenge | False positive on legitimate corrections ("FALSE" used rhetorically) | N-gram signal restricted to direct accusation patterns; not a regex on `wrong` alone |
| Blocking Claude-Code Stop hook | Catastrophic over-fire (see §6.1) | Counter-measures 1–4 above are non-negotiable |
| Framing-aware fix to `verify_document_claim` | Drops TP on third-person discussion shapes | Path A is preferred over Path C (citation-shape restriction); corpus measurement gates the change |
| Durable-artifact checklist (FACT/INFERENCE/UNKNOWN) | Becomes form-without-substance (mode #6) | Already addressed by `epistemic-format.md` rule: labels without engagement are worse than no labels |

### 6.3 Cross-host divergence (confidence-graded)

Grok Build and Claude Code have different hook surfaces. This design explicitly does NOT recommend porting the Claude-Code `StopHook_cross_validator` to Grok Build as a blocking hook, because:

- The Grok-side equivalent would be a `Stop` hook, which is **passive** in Grok. It can inject context but cannot block. Importing the Claude-Code hook shape into Grok without understanding this is the same kind of error as the user's own first example — citing a file shape without verifying the host.

The two hosts therefore get different structural instruments, **graded by confidence in the surfacing mechanism**:

| Host | Structural instrument | Capability | Confidence |
|---|---|---|---|
| Claude Code | `StopHook_cross_validator.py` extension (`mode=block`); `decision: 'block'` returned via stdout JSON (or exit 2) per Claude Code's stop-hook contract | Blocks bad turn | **High** — every cc-aca-epistemic `Stop` invocation exercises the blocking path. Verified at `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/hooks/stop/StopHook_cross_validator.py:380` (prints `{"decision":"block","reason":"..."}` and exits 2). Note this is Claude Code's own contract, **not** Grok's `HookResult` interface — the field name overlaps (`decision`) but the surrounding schema is distinct. |
| Grok Build `UserPromptSubmit` (PR 4) | `HookResult.systemMessage` (USER_HINT) | Human-visible banner; may surface inline to model via the platform adapter | **High** for human-visible delivery (precedent: `handlers/user-message.ts:42`). **Medium-low** for model-consumption — depends on platform surfacing (no in-tree evidence that UserPromptSubmit `systemMessage` is propagated into model input). |
| Grok Build `Stop` (PR 3) | `HookResult.systemMessage` (USER_HINT) | Human-visible banner; model-consumption unverified | **Low / undemonstrated** — `HookResult` is type-permitted (`cli/types.ts:21-34`) and the adapter propagates (`adapters/claude-code.ts:28-42`), but **no `stop.ts` handler exists** in `marketplace-cache/b975999a270027c6/src/cli/handlers/` (8 files verified by `list_dir`). Surfacing is **type-permitted, not demonstrated end-to-end**. Treat PR 3 as best-effort; F4 is the dominant falsifier. |

This is honest about the ceiling. If the user later asks "why does Claude Code block and Grok doesn't," the answer is: *"Because Grok's only blocking event is `PreToolUse`, and these failure modes happen in response text after tool calls complete — and even passive surfacing has not been demonstrated for `Stop` end-to-end in the in-tree marketplace-cache plugin source. The wiki already named the `PreToolUse`-only ceiling; runner source confirms it."*

**Source-vs-doc hierarchy note:** the blocking fact (`PreToolUse` only) is sourced from the doc line (`~/.grok/docs/user-guide/10-hooks.md:99`); the surfacing-mechanism facts (USER_HINT vs MODEL_CONTEXT, `user-message.ts:42`, `session-init.ts:169-172`, handler directory listing) are sourced from runner source. The two sources are not in conflict — they describe different facts.

### 6.4 Latency and measurement cost

- The framing-aware fix to `verify_document_claim` is one regex pass per Stop event — negligible latency.
- The Grok `Stop` injection is one shell-out per Stop event — negligible if the command is `echo`; expensive if it spawns a Python subprocess. Keep it to `echo`/`printf`.
- The held-out corpus measurement is bounded to one engineer-day per gate (§5.2).
- The `/tp` vocabulary extension is one markdown edit — no runtime cost.

---

## 7. What would falsify this design?

A design that cannot be falsified is theater. This design's falsifiers are the **specific observations that would prove the recommended levers are wrong.**

| Falsifier | What it would look like | What we would change |
|---|---|---|
| **F1. Over-fire on legitimate ignorance** | After the blocking gate ships, the model replaces "I cannot tell from the docs alone" with confident fabricated answers to satisfy the gate | Soften the trigger: only block when the turn has zero verification tool calls AND the response contains a knowledge-claim verb (`is`, `does`, `returns`, `defaults to`) |
| **F2. Framing-aware fix drops TP below threshold** | `verify_document_claim` framing fix ships; measurement shows 18/30 TP (below 28/30 floor) | Revert the framing fix; ship in **warn** mode; defer the gate |
| **F3. `/tp` mode 9 (defensive hedging) is too broad** | Users invoke `/tp defensive-hedging` on legitimate steelman updates and the skill agrees it was drift | Narrow mode 9 to a tighter trigger: only when the user's challenge is correct AND the response does not concede in the first sentence |
| **F4. Grok `Stop` injection ignored** | Across 30 held-out sessions, the model's next-turn behavior is indistinguishable from sessions without the injection. Because PR 3's `Stop` is already low-confidence (type-permitted but undemonstrated in-tree per §4.3 / §6.3), this falsifier fires more easily than for PR 4 | Replace the lever: migrate the same payload to a `UserPromptSubmit` hook (which IS demonstrated via `user-message.ts:42`); if even that fails, accept that Grok Build does not have a structural lever for this failure mode and rely on Claude Code only |
| **F5. Corpus too small** | Cannot construct a 30/30 held-out corpus from the available session logs | Defer the gate; the absence of a corpus is itself evidence that the gate is not ready |
| **F6. The model acts on the rules** | After the AGENTS.md rule rewrite ships, session-log analysis shows the model no longer commits the failure modes — the structural levers were not needed | Demote the structural levers to advisory; keep the rule as primary |
| **F7. Cross-host divergence becomes a problem** | The user notices that Grok Build keeps committing #2 while Claude Code (running `verify_document_claim`) blocks it, and asks why Grok can't just block too | Acknowledge the host ceiling and decide whether the user wants to switch hosts for these sessions — do not silently disable the Claude-Code gate to "match" |
| **F8. Subagent review latency dominates** | High-stakes turns take 10× longer because every response is reviewed | Restrict subagent review to a sample (every Nth turn) or to user-flagged turns only |

The single most important falsifier is **F1** — over-firing pushes the model toward confident fabrication, the opposite of the goal. If F1 happens, the gate must be softened or removed, not strengthened.

---

## 8. Implementation sequencing (summary, detailed in PR Plan)

The levers ship in this order, each independently reviewable:

1. **Document** — write this design doc (already done).
2. **Skill vocabulary** — extend `/tp` with modes 7, 8, 9. Lowest blast radius; gives the user a sharper diagnostic instrument immediately.
3. **Grok passive injection** — `Stop` and `UserPromptSubmit` hooks at `~/.grok/hooks/`. Cheap; cannot over-fire (passive).
4. **Claude-Code detector extension** — add `verify_ignorance_claim` and framing-aware fix to `StopHook_cross_validator.py`. **Advisory until measured.**
5. **Measurement** — run the held-out corpus against the new detector. If threshold met, promote to `mode=block`. If not, keep advisory.
6. **Durable-artifact checklist enforcement** — only if measurement shows the model is not internalizing the FACT/INFERENCE/UNKNOWN labels from `epistemic-format.md`. Otherwise this is already in place.

The order is deliberate: passives and skill vocabulary ship first because they cannot over-fire. The blocking Claude-Code gate ships last and only ships at all if measurement proves it works.

---

## 9. Key Decisions (summary)

Detailed in §10 below. Headlines:

1. **Reframe as rule non-firing, not missing rules.** The three failure modes are already named; the levers must enforce the existing rules, not add new ones.
2. **Different levers per failure mode.** #1 and #2 get blocking-capable structural levers; #3 gets a user-invoked diagnostic extension (`/tp` mode 9) and passive injection — NOT a blocking gate, because over-firing on #3 is catastrophic.
3. **Reuse, do not rebuild.** Extend `StopHook_cross_validator.py` (already exists, already has tool-event log lookup) and extend `/tp` (already has argument-routed mode vocabulary) rather than building parallel systems.
4. **Every gate is advisory until measured.** Per workspace rule, no blocking gate ships without a held-out corpus at ≥28/30 TP and ≤2/30 FP.
5. **Honest about the host ceiling.** Grok Build cannot block response-text failure modes because only `PreToolUse` blocks. This is documented and accepted; the design does not pretend otherwise. **Additionally, even passive surfacing for `Stop` is type-permitted by `HookResult` but undemonstrated end-to-end in the marketplace-cache plugin source — `Stop` injection is best-effort, not guaranteed.** (See §11 Decision 5 addendum for the canonical restatement.)
6. **The catastrophic risk is over-firing.** A claim-discipline gate that blocks "I cannot tell" without checking for prior verification pushes the model toward confident fabrication. Counter-measures 1–4 in §6.1 are non-negotiable with any blocking gate.

---

## 10. PR Plan

PRs are ordered so each is independently mergeable. Each names its kind (doc / AGENTS.md / skill / hook-json / code), files affected, dependencies, and a brief description.

### PR 1 — Design document (doc)

- **Title:** `docs: grok claim-discipline design (d9e5a3f8)`
- **Kind:** doc
- **Files:** `P:/docs/grok-claim-discipline-design-d9e5a3f8.md`, `P:/tmp/grok-design-d9e5a3f8/summary.md`
- **Dependencies:** none
- **Description:** This document. Establishes the problem reframe, the lever menu, the measurement rule, and the falsifiers. No code or behavior changes.

### PR 2 — `/tp` skill vocabulary extension (skill)

- **Title:** `skills(tp): add drift modes 7 (premature termination), 8 (evidence confabulation), 9 (defensive hedging)`
- **Kind:** skill
- **Files:** `C:/Users/brsth/.grok/skills/tp/SKILL.md`, `C:/Users/brsth/.grok/skills/tp/protocol.md`
- **Dependencies:** PR 1 (this design) for grounding
- **Description:** Add three rows to the failure-mode vocabulary table. Extend the Falsifier clause to cover the new modes. Update `protocol.md` §15 (Failure modes a partner must self-monitor) to include the new entries. No new plumbing; the existing `/tp <mode>` argument routing handles the new modes automatically.
- **Review focus:** the mode definitions match the failure shapes in §2 of the design doc; the Falsifier clause does not become a recital.

### PR 3 — Grok passive injection hook: claim-discipline Stop warn (hook-json)

- **Title:** `grok-hooks: claim-discipline-stop-warn (passive, best-effort)`
- **Kind:** hook-json
- **Files:** `C:/Users/brsth/.grok/hooks/claim-discipline-stop-warn.json`, `C:/Users/brsth/.grok/hooks/claim-discipline-stop-warn.sh`
- **Dependencies:** PR 1
- **Description:** A `Stop` event hook that scans the just-finished turn for ignorance-claim and document-claim regex triggers. On match, returns a `HookResult` via stdout JSON containing `systemMessage: "Last turn matched the premature-termination or evidence-confabulation trigger. Verify sources before citing in the next turn."`. The runner propagates `systemMessage` via the platform adapter's `formatOutput` (`marketplace-cache/b975999a270027c6/src/cli/adapters/claude-code.ts:28-42`); no event-type gating. Channel: **USER_HINT**. **Precision note:** `Stop` is type-permitted by `HookResult` but undemonstrated end-to-end in the in-tree marketplace-cache plugin source (no `stop.ts` handler in `src/cli/handlers/`). Treat as best-effort; F4 is the dominant falsifier.
- **Review focus:** the script is fail-open; the regex is conservative; the script does NOT write to a session-scoped file (Claude Code's pattern, not Grok's); no `decision` field is emitted (irrelevant for `Stop`).

### PR 4 — Grok passive injection hook: corrective-challenge UserPromptSubmit (hook-json)

- **Title:** `grok-hooks: corrective-challenge-injection (passive, demonstrated)`
- **Kind:** hook-json
- **Files:** `C:/Users/brsth/.grok/hooks/corrective-challenge-injection.json`, `C:/Users/brsth/.grok/hooks/corrective-challenge-injection.sh`
- **Dependencies:** PR 1
- **Description:** A `UserPromptSubmit` event hook that scans the user's message for corrective-challenge signals (`FALSE`, `wrong`, `you're not addressing`, `that's not what I said`, `nope`). On match, returns a `HookResult` via stdout JSON containing `systemMessage: "User issued a corrective challenge. Consider whether drift occurred before responding."`. The runner propagates via the platform adapter; precedent: `marketplace-cache/b975999a270027c6/src/cli/handlers/user-message.ts:42`. Channel: **USER_HINT**. Cannot block. **Neutral text — does NOT auto-suggest `/tp`** (per Decision 7, `/tp` is user-invoked).
- **Review focus:** signal set is tight (not a regex on `wrong` alone); cannot leak user-message content into a globally-readable file; the `systemMessage` payload must not contain the user's message text verbatim (privacy).

### PR 5 — Claude-Code `StopHook_cross_validator.py`: add `verify_ignorance_claim` (code, advisory)

- **Title:** `cc-aca-epistemic: add verify_ignorance_claim (advisory)`
- **Kind:** code
- **Files:** `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/hooks/stop/StopHook_cross_validator.py`, `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/__lib/claim_patterns.py`, `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/tests/test_epistemic_plugin.py`
- **Dependencies:** PR 1, PR 2
- **Description:** Add a new function `verify_ignorance_claim(data)` parallel to `verify_document_claim`. Same tool-event log lookup. Block if ignorance-claim pattern matches AND no verification tool (Read, Grep, Bash with read-like commands, WebSearch) ran in the turn. Ships in **advisory / warn** mode by default; the `STOP_CROSS_VALIDATOR_MODE=block` env override does not promote it to block automatically. Block mode requires measurement PR 6.
- **Review focus:** the new detector uses the same evidence lookup as `verify_document_claim` (no parallel state); the block reason string tells the model what to do instead ("search, then re-state"); the regex is conservative.

### PR 6 — Held-out corpus measurement (measurement, code)

- **Title:** `cc-aca-epistemic: measured_tp_on_corpus for claim-discipline gates`
- **Kind:** code + measurement
- **Files:** `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/tests/test_held_out_corpus.py`, `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/__lib/corpus_labeler.py`, a CSV/JSONL corpus file
- **Dependencies:** PR 5
- **Description:** Build a 60-turn held-out corpus from the labeled sources in §5.1. Run `verify_document_claim` (current) and `verify_ignorance_claim` (new) against it. Report TP/FP/FN/TN. Gate the framing-aware fix on ≥28/30 TP AND ≤2/30 FP. If the threshold is not met, the gate stays advisory and the PR comments explicitly name which shapes are missed.
- **Review focus:** the corpus is held-out (not the same as the author-constructed test suite — count per §5.2); the labeling is reproducible (deterministic regex or two-annotator agreement); the threshold is the workspace rule, not lower.
- **Expected outcome:** this is the PR most likely to discover that the trigger needs softening. The result, not the implementation, determines whether the blocking gate ever ships.

### PR 7 — Promote to block mode (conditional on PR 6)

- **Title:** `cc-aca-epistemic: promote claim-discipline to mode=block (gated on PR 6)`
- **Kind:** code
- **Files:** `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/hooks/stop/StopHook_cross_validator.py`, `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/__lib/claim_patterns.py`
- **Dependencies:** PR 6 with threshold met
- **Description:** Wire `verify_ignorance_claim` into the `Stop` aggregator. Update the runtime env to `STOP_CROSS_VALIDATOR_MODE=block` only for `verify_ignorance_claim`. **Skip this PR entirely if PR 6 does not meet the threshold.**
- **Review focus:** the catrastrophic-over-fire counter-measures from §6.1 are present (block message is constructive, circuit breaker on block frequency, never blocks on `UserPromptSubmit`).

### PR 8 — Framing-aware fix to `verify_document_claim` (conditional on PR 6)

- **Title:** `cc-aca-epistemic: framing-aware fix to verify_document_claim`
- **Kind:** code
- **Files:** `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/__lib/claim_patterns.py`, `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/hooks/stop/StopHook_cross_validator.py`
- **Dependencies:** PR 6 with threshold met for the new framing-aware variant
- **Description:** Apply Path A from `P:\.data\wiki\concepts\confabulated-ignorance-and-source-fabrication-gate.md` (split first-person from third-person patterns, or add a negative-signal window for third-person meta-discussion markers). **Skip this PR entirely if the framing-aware variant drops TP below the threshold on the held-out corpus.**
- **Review focus:** the negative-signal list is a fixed curated set (not an open regex); the framing fix does not weaken the fabrication-detection TP below the floor.

### PR 9 — Verification: live session smoke test (measurement)

- **Title:** `docs: claim-discipline live-session smoke results`
- **Kind:** doc + measurement
- **Files:** `P:/docs/claim-discipline-smoke-2026-XX.md`, supporting JSONL in `P:/tmp/`
- **Dependencies:** PRs 2–5 in production
- **Description:** Run 5–10 live Grok Build sessions and 5–10 live Claude Code sessions with the levers enabled. Document: (a) did the model commit any of the three failure modes, (b) did the passive injection influence next-turn behavior, (c) did the blocking gate fire correctly, (d) did any of the catastrophic-over-fire counter-measures trip. Honest report even if the answer is "no measurable effect."
- **Review focus:** the report is honest about null results; null results are acceptable and inform whether further levers are needed.

### PR 10 — Durable-artifact checklist enforcement (conditional on PR 9)

- **Title:** `docs/claude-rules: durable-artifact checklist enforcement (conditional)`
- **Kind:** doc (rule)
- **Files:** `P:/.claude/rules/epistemic-format.md` (amend), `~/.grok/AGENTS.md` (cross-reference)
- **Dependencies:** PR 9 showing that `epistemic-format.md` labels are not internalized
- **Description:** Only if PR 9 shows the model is not using FACT/INFERENCE/UNKNOWN labels automatically, add a tighter rule: *"For any material claim, write the label inline before the prose."* Otherwise, this PR is skipped — the existing rule is sufficient.
- **Review focus:** does not become mode 6 (performative rigor); the labels are paired with engagement, not substituted for it.

---

## 11. Key Decisions

The most important architectural/design decisions, each with brief rationale and the alternative rejected.

### Decision 1 — Reframe as rule non-firing, not missing rules

**Chosen:** Treat the failure as rules-not-firing. Push structural levers (hooks, skills) that *enforce* existing rules rather than write new ones.

**Rejected alternative:** Add three new rules to `AGENTS.md` covering #1/#2/#3.

**Rationale:** The binding reframe explicitly forbids cargo-cult rule-addition. The existing rules already name the failure modes; adding more rules compounds the rule-non-firing problem. The structural lever is a different category of fix, not a stronger version of the same fix.

**Caveat — text-shaped levers in PR 3 / PR 4 are not a full escape from Decision 1:** the Grok passive injection hooks (PR 3 and PR 4) return text guidance that the model can absorb or ignore. They are *more* structurally anchored than an `AGENTS.md` rule (because the runner surfaces them in-channel via `HookResult.systemMessage`), but they are still text-shaped and still operate on the model's good-faith compliance. The workspace previously documented this exact limitation: `P:/.data/wiki/concepts/hook-architecture.md:27` records *"v2 (2025): Shifted to blocking hooks after finding injection easily ignored"*. Treat PR 3 / PR 4 as a **low-cost hedge**, not as a high-confidence primary lever. The Claude Code `StopHook_cross_validator` extension (PRs 5–8) carries the primary load on the blocking side; the `/tp` vocabulary extension (PR 2) is a diagnostic instrument that requires a human to invoke it.

**Decision axis:** intervention category (rule-text vs. structural-enforcement), with explicit acknowledgment that some structural levers are themselves text-shaped and inherit the prior art's effectiveness ceiling.

### Decision 2 — Different levers for #1/#2 vs. #3

**Chosen:** #1 and #2 get blocking-capable structural levers (Claude-Code `Stop` hook). #3 gets only passive injection and `/tp` vocabulary extension; no blocking gate.

**Rejected alternative:** Build a unified blocking gate for all three modes using a sophisticated detector that does turn-history tracking.

**Rationale:** Per the existing wiki, #3 is "type: agent territory" — pattern matching cannot reliably detect rhetorical pivots across turns. A blocking gate on #3 would have an unacceptable FP rate against legitimate steelman updates. The catastrophic risk (§6.1) is amplified for #3 because the false-positive shape (legitimate concession that looks like a defensive pivot) is more common than the true-positive shape (sophisticated defense).

**Decision axis:** false-positive tolerance vs. coverage. We accept lower coverage on #3 to avoid catastrophic over-firing.

### Decision 3 — Reuse `StopHook_cross_validator.py` and extend `/tp`; do not build parallel systems

**Chosen:** Extend `StopHook_cross_validator.py::verify_document_claim` to add `verify_ignorance_claim` and the framing-aware fix. Extend `/tp` SKILL.md with three new drift modes.

**Rejected alternative:** Build a new plugin `cc-claim-discipline` with fresh patterns and a new skill `/claim-discipline`.

**Rationale:** Per the workspace's AAR framing, "reuse-derived" is the highest-leverage, lowest-blast-radius option. The existing `StopHook_cross_validator.py` already has tool-event log lookup, the dispatch wiring, and the test infrastructure. The existing `/tp` already has argument-routed mode vocabulary, the five-line circuit breaker, and a documented Falsifier clause. Parallel systems double the surface area and dilute the diagnostic vocabulary.

**Decision axis:** surface-area growth vs. marginal capability gain. Reuse wins because the marginal capability (a fourth "I cannot tell" detector or a fourth drift mode) does not justify the parallel-system overhead.

### Decision 4 — Every blocking gate is advisory until `measured_tp_on_corpus` meets threshold

**Chosen:** No blocking gate ships without a held-out corpus showing ≥28/30 TP AND ≤2/30 FP.

**Rejected alternative:** Ship the blocking gate immediately based on author-constructed tests, then measure in production.

**Rationale:** Per the workspace rule, a gate that fires 0 real positives stays advisory. Author-constructed tests have selection bias toward the failure shape the author had in mind. Task #1123 (already documented) is a concrete example of an author-constructed FP that survived the wiki's historical test suite for `verify_document_claim` and only surfaced in production. (The historical wiki figure was 23; the actual count scoped to `test_quote_exemption_gates.py` alone is 19, and the whole `tests/` directory is 205, both as of 2026-07-18 — see §5.2 for the current volatile counts and verification command.) The 28/30 + ≤2/30 threshold is the workspace's pre-committed acceptance criterion; this design does not negotiate it.

**Decision axis:** time-to-ship vs. measured-correctness. Correctness wins because the failure mode is the model committing unsignaled false claims; shipping an unmeasured gate would itself be an unsignaled claim.

### Decision 5 — Honest about the host ceiling (response text not blockable in Grok)

**Chosen:** Acknowledge that Grok Build cannot block response-text failure modes. Ship passive injection hooks on the Grok side; ship blocking hooks on the Claude Code side.

**Rejected alternative:** Pretend Grok hooks can block response text by writing a `Stop` hook with a deny decision. Or pretend the AGENTS.md rule alone is enough on the Grok side.

**Rationale:** The hook doc (line 99) and the existing wiki are aligned: only `PreToolUse` blocks. Stop hooks are passive in Grok. Honesty about this is required by the binding reframe ("do not pretend Grok hooks give block-level enforcement for response text"). Pretending otherwise would be the same kind of error as the user's original failure #2 — citing a hook shape without verifying the host behavior.

**Addendum (parallel-structure with §9 item 5):** The blocking fact (response-text not blockable) is half the ceiling. The other half is that even passive surfacing for `Stop` is type-permitted by `HookResult` but undemonstrated end-to-end — see §4.3 precision note. `UserPromptSubmit` passive surfacing is demonstrated via `handlers/user-message.ts:42`; `Stop` is not. The PR plan treats PR 3 (Stop) as best-effort and PR 4 (UserPromptSubmit) as the demonstrated channel. This consideration is part of Decision 5's host-accurate-instrumentation axis, not a separate decision.

**Decision axis:** single-host uniformity vs. host-accurate instrumentation. Host-accurate wins because the user will eventually notice if Grok and Claude Code diverge and ask why; honest engineering beats silent inconsistency.

### Decision 6 — Catastrophic-over-fire counter-measures are non-negotiable

**Chosen:** Any blocking gate ships with the four counter-measures from §6.1: only block when no verification tool ran, constructive block message, circuit breaker on block frequency, never block on `UserPromptSubmit`.

**Rejected alternative:** Ship the blocking gate "lightly" first and add counter-measures later.

**Rationale:** The catastrophic risk (over-firing pushes the model toward confident fabrication) is the worst possible outcome of a claim-discipline gate. Adding counter-measures "later" means the gate runs at least once in the dangerous configuration. That is the original problem in miniature — shipping without measurement and discovering the failure in production.

**Decision axis:** ship-fast vs. ship-safe. Ship-safe wins because the failure shape (confident fabrication) is harder to detect than the failure shape we are trying to prevent.

### Decision 7 — The `/tp` skill is user-invoked; do not auto-fire it

**Chosen:** Extend `/tp` with three new drift modes; keep the user-invoked design. Do not write a hook that auto-invokes `/tp`.

**Rejected alternative:** Write a `Stop` hook that always runs the five-line circuit breaker on the prior turn.

**Rationale:** The `/tp` SKILL.md explicitly states: *"Not a hook. Does not auto-fire. The user notices drift and invokes it. Auto-firing would make it noise."* Auto-firing `/tp` would conflict with the existing design intent. The passive injection in PR 4 (`corrective-challenge-injection`) is a softer nudge — it tells the user "consider `/tp defensive-hedging`" rather than running the diagnostic automatically.

**Decision axis:** auto-coverage vs. diagnostic precision. The diagnostic precision of user-invoked `/tp` is higher because the user has context on whether the prior turn was drift; auto-firing dilutes that.

---

## 12. Open questions (not blocking; surfaced for the next session)

1. **Cursor / Codex hosts:** this design covers Grok Build and Claude Code only. Cursor's `beforeSubmitPrompt` and Codex's hook surface may have different ceilings. **Not blocking — out of scope for d9e5a3f8, but should be re-evaluated if the user runs the same task in those hosts.**
2. **Subagent review threshold:** PR 9 may show that subagent review of high-stakes turns catches #3 better than the passive injection. The threshold for "high-stakes" is not specified in this design and is left as a follow-up.
3. **Catalog-vs-runtime gap:** the design assumes the user's prior bad-session transcript is recoverable. If it is not in the corpus sources in §5.1, the measurement PR cannot label it as TP ground truth and must rely on user-supplied labels. Worth confirming before PR 6.
4. **Grok hook documentation drift:** the hook doc is the source of truth for "only PreToolUse blocks." If a future Grok release adds `block: true` semantics to `Stop`, this design's levers can be promoted from passive to blocking on the Grok side without further changes — the only impact is that PR 3 and PR 4 become blocking-capable. Worth a periodic re-check against `~/.grok/docs/user-guide/10-hooks.md`.
5. **Handler directory coverage:** also re-check `C:/Users/brsth/.grok/marketplace-cache/<hash>/src/cli/handlers/` on each Grok update. Handler coverage is the **authoritative source of which events are demonstrated end-to-end** in the marketplace-cache plugin source. As of 2026-07-18 there is no `stop.ts` handler (verified by `list_dir` — 8 files: `context.ts`, `file-context.ts`, `file-edit.ts`, `index.ts`, `observation.ts`, `session-init.ts`, `summarize.ts`, `user-message.ts`). If a future plugin release adds `stop.ts`, PR 3's `Stop` injection can be promoted from type-permitted to demonstrated; until then, treat it as best-effort and measure per §5.

---

*End of design document.*