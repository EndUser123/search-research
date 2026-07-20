---
thread_id: plausible-narratives-substitute-for-verification-20260720
parent_handoff_path: P:/docs/handoffs/design-skill-runtime-foundation-20260720/HANDOFF.md
current_session_id: 019f8082-9298-7561-b03e-3c21afc43115
current_terminal_id: console_fb11bbd2-b737-48d8-bbcc-d06b
produced_at: 2026-07-21T01:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: n/a
---

# HANDOFF — Plausible narratives substitute for verification

## 1. Objective

Identify, document, and address the root cognitive failure pattern observed across the 2026-07-20 session: the model constructs plausible narratives that feel like answers, which causes it to stop verifying — even when the narrative is wrong.

## 2. Status

**OPEN** — pattern identified, root cause named, structural fix proposed but not implemented. This handoff exists so the next session can act on it.

## 3. Producing context

- Date: 2026-07-20
- Session: `019f8082-9298-7561-b03e-3c21afc43115`
- Terminal: `console_fb11bbd2-b737-48d8-bbcc-d06b`
- Session length: ~full day, multiple subsystems touched

## 4. Read-first list

1. This handoff — the pattern, instances, and proposed fix
2. `P:/AGENTS.md` "Observe-Before-Propose" section (lines 190-228) — existing rule that was repeatedly broken
3. `P:/AGENTS.md` "Host runtime: Grok Build" section (lines 30-62) — existing rule that was repeatedly broken
4. `P:/.claude/CLAUDE.md` "Absence Conclusions" section — existing rule that was repeatedly broken
5. `C:/Users/brsth/.grok/docs/user-guide/07-mcp-servers.md` lines 200-213 — the documentation I should have read before concluding MCP config doesn't exist

## 5. Verified facts

- [FACT] The model dismissed a correct finding (MCP not enumerated) because its proposed fix was wrong (read `[mcp_servers]` from config.toml — that section doesn't exist). The finding and the fix are separate claims; the model conflated them and threw out both. (Session transcript: the user forwarded the other LLM's finding; the model checked config.toml, found no `[mcp_servers]`, concluded "the data doesn't exist.")

- [FACT] MCP config IS in static files — specifically `~/.claude.json` (3 servers: web-search-prime, minimax-search, perplexity) and `~/.claude/.mcp.json` (1 server: context7). Documented at `~/.grok/docs/user-guide/07-mcp-servers.md:200-213` under "Compatibility." (`~/.claude.json` verified directly; documentation read directly.)

- [FACT] The model checked `~/.claude/settings.json` (wrong file) instead of `~/.claude.json` (the Claude Code top-level config). These are different files. `settings.json` has `mcpServers: {}` (empty). `.claude.json` has `mcpServers: {web-search-prime, minimax-search, perplexity}`. (Both files inspected directly.)

- [FACT] The model constructed a narrative ("the hook fires before MCP servers connect, so enumeration is structurally impossible") that felt like an answer. The narrative was wrong — MCP config is in static files that the script can read. The narrative substituted for reading the documentation. (Session transcript: model response to the other LLM's finding.)

## 6. Current state

### The pattern (observed 5+ times in one session)

The model encounters a claim it can't immediately verify. Instead of reading documentation or searching for evidence, it:

1. Constructs a plausible narrative explaining why the claim is wrong / the data doesn't exist / the approach can't work
2. The narrative feels sufficient ("structurally impossible," "the hook fires before X")
3. The model presents the narrative as its answer
4. The narrative is wrong, but the model doesn't discover this until the user pushes back or external evidence arrives

### Instances this session

| # | Instance | The plausible narrative | The reality |
|---|----------|------------------------|-------------|
| 1 | Claude hooks not firing | "The hooks are wired in settings.json, they must be firing" | `compat.claude.hooks=false` — hooks NOT firing |
| 2 | proposal-grounding-monitor | "I'm proposing to build Observe-Before-Propose from scratch" | It already existed, fully built, 111 tests, orphaned in `~/.grok/plugins/` |
| 3 | MCP not enumerated | "The hook fires before MCP connects, enumeration is structurally impossible" | MCP config is in `~/.claude.json` and `.mcp.json`, documented at `07-mcp-servers.md:200-213` |
| 4 | C1/C2 durability oscillation | "Provenance matters, durability is the right answer" | The user's wiki already absorbs decisions as concepts; durability was over-engineering |
| 5 | adv-review references | "I don't know why adv-review exists" (acceptable) but proposed to delete without checking why it was built | It was a stub for a runner that was never implemented |

### The root cause (strategic, not tactical)

**Plausible narratives override rules.** The workspace has rules that would prevent each instance:
- "Observe-Before-Propose" (AGENTS.md:190-228) — inspect existing patterns before proposing
- "Host runtime: Grok Build" (AGENTS.md:30-62) — verify against Grok docs before assuming
- "Absence Conclusions" (CLAUDE.md) — don't conclude something is missing without checking obvious sources

The model broke all three repeatedly. The problem isn't missing rules. It's that **when a plausible narrative forms, the model treats the narrative as sufficient and stops applying the rules.** The narrative makes the rules feel unnecessary.

## 7. Task packets

### PNV-01: Internalize the narrative-as-signal rule

- **goal:** when the model catches itself constructing a narrative for why something can't be done/found/known, use that as the trigger to read documentation — not as the answer
- **in scope:** add the rule to AGENTS.md as a named pattern, distinct from Observe-Before-Propose
- **out of scope:** building a hook to enforce it (hooks are prompt-advisory; the pattern is cognitive)
- **files / anchors:** `P:/AGENTS.md` — add after "Observe-Before-Propose" section
- **acceptance:** next session, when the model encounters a claim it can't verify, it reads documentation before constructing a dismissal narrative
- **falsifier:** if the model constructs another plausible narrative that turns out wrong, the rule didn't land hard enough
- **verification level required:** LIVE_BEHAVIOR
- **no_live_run_reason:** not deferred — the next session IS the live test

### PNV-02: Separate findings from fixes (anti-conflation)

- **goal:** when evaluating an external review or critique, evaluate the finding and the proposed fix independently — a wrong fix does not invalidate a correct finding
- **in scope:** add the rule to AGENTS.md
- **out of scope:** changing review skill mechanics
- **files / anchors:** `P:/AGENTS.md` — add near "Review Discipline" section
- **acceptance:** when the model receives a finding with a wrong fix, it investigates the finding independently before dismissing it
- **falsifier:** if the model conflates finding+fix again, the rule failed
- **verification level required:** LIVE_BEHAVIOR

## 8. Open decisions

### Decision 1: Is a new rule the right intervention?

**Question:** AGENTS.md already has Observe-Before-Propose and Absence Conclusions. Both were broken. Will another rule help, or is this a different kind of problem?

**Options:**
- **A: Add a new, more specific rule.** Name the pattern ("plausible narratives substitute for verification"), give the MCP instance as a worked example. The specificity makes it harder to rationalize past.
- **B: Strengthen the existing rules.** Observe-Before-Propose already says "inspect existing patterns before proposing." Add a clause: "this includes reading documentation when you're about to claim something doesn't exist."
- **C: Both.** New rule for the pattern + strengthen existing rules with the specific failure instances.

**Currently leading:** Option C. The pattern is distinct from Observe-Before-Propose (which is about proposing structures) — it's about dismissing findings. And it's distinct from Absence Conclusions (which is about not finding things) — it's about WHY you stop looking. Naming it specifically helps.

### Decision 2: Should this become a wiki concept?

**Question:** "Plausible narratives substitute for verification" is a generalizable cognitive pattern that applies beyond this workspace. Should it be promoted to `P:/.data/wiki/concepts/`?

**Options:**
- **Yes — promote as a concept.** Future sessions searching the wiki for "why did the model get this wrong" would find it.
- **No — keep as a handoff.** The pattern is specific to this session's instances; it doesn't need to be a permanent concept until it recurs across sessions.

**Currently leading:** No. One session isn't enough evidence that this is a durable pattern vs. a bad day. If it recurs in the next session, promote then.

## 9. Hard constraints

1. The rule must be actionable, not abstract. "Be more careful" is not actionable. "When you catch yourself constructing a narrative for why X can't be done, read the documentation for X" is actionable.
2. The rule must include a worked example from this session (the MCP instance is the clearest).
3. The rule must not duplicate Observe-Before-Propose or Absence Conclusions — it must address the specific gap (narrative-as-substitute-for-verification) that those rules don't cover.

## 10. Other outstanding streams

- **M1 system** — shipped with MCP fix applied. All code-review findings addressed. `/check` PASS. See parent handoff.
- **proposal-grounding-monitor** — evaluation handoff written at `P:/docs/handoffs/proposal-grounding-monitor-evaluation-20260720/HANDOFF.md`. Ready to enable.
- **/design skill improvements** — shipped (Step 4.5, 5.5, 6.0, 6d). Untested in real run. See parent handoff.
- **Review skill consolidation** — routing table shipped, 2 skills deprecated. See parent handoff.

## 11. Explicit non-goals

- Do NOT build a hook to enforce this pattern. It's cognitive, not mechanical. Hooks enforce tool-call sequences; they can't detect internal narrative construction.
- Do NOT re-litigate the session's other failures. This handoff captures the pattern, not a catalog of every mistake.
- Do NOT promote this to a wiki concept until it recurs in a future session.

## 12. Resumption protocol

1. Read this handoff
2. Read `P:/AGENTS.md` lines 190-228 (Observe-Before-Propose) and lines 30-62 (Host runtime)
3. Decide: add a new rule (PNV-01 + PNV-02) or strengthen existing rules
4. Write the rule with the MCP worked example
5. In the next real work: when constructing a dismissal narrative, check whether you've read the documentation first. If not, read it.

## 13. Suggested next invocation

```
Add a rule to P:/AGENTS.md about plausible narratives substituting for
verification. The pattern: the model constructs a plausible story for why
something can't be done/found/known, the story feels like an answer, and
the model stops investigating. The story is often wrong. Fix: treat the
narrative as the signal to read documentation, not as the answer. Include
the MCP instance as a worked example (model said "enumeration is
structurally impossible" without reading 07-mcp-servers.md which documents
the sources).
```

## 14. Last user message (verbatim)

> "what's the root cause of that miss we had?"

## 15. Epistemic labels

- [FACT] All 5 instances verified against session transcript and source files
- [FACT] MCP config location verified by reading `~/.claude.json` and `07-mcp-servers.md`
- [FACT] Existing rules (Observe-Before-Propose, Absence Conclusions) were present in AGENTS.md / CLAUDE.md at the time of each failure
- [INFERENCE] The pattern is "plausible narratives override rules" rather than "the model doesn't know the rules" — the rules exist and were written by the model itself in this session
- [INFERENCE] The fix is to make the narrative itself the trigger for verification, not to add more rules that the narrative can override
- [UNKNOWN] Whether a new rule will be more effective than the existing ones at preventing recurrence
