---
title: "Compat-layer cargo-cult — porting rules without evaluating necessity"
created: 2026-07-28
source: session-019fa48a (/aar Phase 4 cluster analysis)
tags: [cargo-cult, compat-layer, claude-to-grok, porting, anti-pattern, observe-before-propose]
host: both
agent: grok
verification: observed
cognitive_load: 2
summary: >
  When porting rules from Claude compat files to Grok-native files, the model
  defaulted to preserving content rather than evaluating necessity. 8 rules were
  ported; 7 were duplicated (already in Grok files) or Claude-Code-specific (not
  relevant on Grok Build). Only 1 rule (replacement default) was genuinely unique.
  The operator caught this with "were those claude additions useful or just
  cargo-cult?" The pattern: porting without asking "is this already covered?"
  is the same failure class as adding code without searching for existing
  implementations.
relations:
  - target: wiki/concepts/grok-build-host-authority.md
    type: related
  - target: wiki/concepts/disabling-claude-compat-instruction-loading.md
    type: related
  - target: wiki/concepts/agents-md-construction-best-practices.md
    type: related
---

# Compat-layer cargo-cult — porting rules without evaluating necessity

## Decision context

**Why this was needed:** when disabling Claude compat instruction loading (`compat.claude.agents = false`), the model ported 8 rules from the Claude files into `~/.grok/AGENTS.md` to "preserve unique content." The operator asked: "were those claude additions useful or just cargo-cult?" Evaluation revealed 7 of 8 were either duplicated (already in the Grok files) or Claude-Code-specific (not relevant on Grok Build). Only 1 rule (replacement default) was genuinely unique and worth porting.

## The pattern

When moving content from one system to another (compat files to native files, Claude to Grok, one skill to another), the default behavior is **preservation** — copy everything, evaluate later. This is driven by:

1. **Loss aversion** — fear of losing something that might be needed
2. **Fast execution bias** — porting is faster than evaluating each rule
3. **Absence of a check step** — no "is this already covered?" gate before porting

The result: content that's duplicated across files (inflating instruction budget) or irrelevant to the target system (adding noise without value).

## The specific instance (session 019fa48a)

When `compat.claude.agents = false` was set, 8 rules were ported from the Claude files into `~/.grok/AGENTS.md`:

| Rule ported | Already in Grok files? | Relevant on Grok Build? | Verdict |
|-------------|----------------------|------------------------|---------|
| `__lib` naming | No, but Claude-specific | Only for marketplace packages | Cargo-cult |
| Python type hints always | Partially | Universal but model defaults to it | Cargo-cult |
| `pytest --cov` >80% | No | Arbitrary threshold without justification | Cargo-cult |
| Cost tiering | Yes (in P:\AGENTS.md + nemotron directive) | Duplicated | Cargo-cult |
| Replacement default | **No** | **Universal principle** | **Kept** |
| Sequential file operations | Yes (in file editing protocol) | Duplicated | Cargo-cult |
| Multi-component validation | Partially | Standard practice | Cargo-cult |
| Performance optimizations | No | Niche, better as wiki | Cargo-cult |

7 of 8 were stripped. The operator's question — "useful or just cargo-cult?" — was the evaluation gate that should have run before porting, not after.

## The fix

Apply the same "search before proposing" principle to porting:
1. For each rule being considered for porting, check: **is this already in the target file?**
2. If yes: skip (it's duplicated)
3. If no: check **is this relevant to the target system?** (Claude-Code-specific conventions like `__lib`, `plugin.json`, `TaskCreate` schema are not relevant on Grok Build)
4. If relevant and unique: port it
5. If neither: skip

This is the "observe before propose" pattern from `P:\AGENTS.md` applied to the porting context. The same principle: don't add without first checking what already exists.

## Connection to broader principles

This is the same failure class as:
- **Adding code without searching for existing implementations** (AGENTS.md "Search before proposing")
- **Inventing a structure without inspecting existing patterns** (P:\AGENTS.md "Observe-Before-Propose")
- **Assuming Claude Code features work on Grok Build** ([[grok-build-host-authority]])

In all cases, the model defaults to action (add/port/implement) before evaluation (is this needed? does this already exist? is this relevant?). The structural fix is the same in all cases: a mandatory check step before the action.

## What this means for our workspace

When porting content between files, systems, or hosts:
1. **Evaluate before porting** — for each item, check if it's already covered in the target
2. **Strip Claude-Code-specific conventions** — `__lib`, `plugin.json`, `pyproject.toml`, `TaskCreate` schema are Claude marketplace conventions, not universal
3. **The replacement default test** — if a rule from the source file is the ONLY place it appears across all loaded files AND it's relevant to the target system, port it. Otherwise skip.

## Falsifier

This pattern is wrong if ported rules consistently turn out to be unique and necessary. Test: on the next compat migration, evaluate each rule before porting and track how many are genuinely unique vs duplicated. If >80% are unique, the evaluate-first step is overhead.

## Receipts

- Session 019fa48a: 8 rules ported from Claude files, 7 evaluated as cargo-cult by operator, stripped to 1
- The 1 surviving rule (replacement default) passed both the uniqueness check (not in any Grok file) and the relevance check (universal principle, not Claude-specific)

## Relations

- [[grok-build-host-authority]] — the broader principle of not assuming cross-host transferability
- [[disabling-claude-compat-instruction-loading]] — the config decision that triggered the porting
- [[agents-md-construction-best-practices]] — progressive disclosure principle
