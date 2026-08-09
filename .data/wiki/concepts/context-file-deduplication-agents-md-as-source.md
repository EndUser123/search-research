---
title: "Context file deduplication: AGENTS.md as source of truth, Claude files as include stubs"
created: 2026-07-21
source: session-2026-07-21
tags: [context-engineering, agents-md, claude-md, deduplication, grok-build, compat-layer, cross-tool, single-source-of-truth]
summary: >
  Multi-tool workspaces accumulate duplicate context files (AGENTS.md +
  CLAUDE.md + bundled copies) when multiple harnesses (Claude Code, Codex,
  Cursor, Grok Build) each discover their own format. The compat-layer
  toggle is the wrong frame — the right frame is single-source-of-truth
  per layer (user, workspace, rules), with non-canonical files becoming
  thin `@`-include stubs. ETH Zurich (Feb 2026) found context files
  actively hurt agent performance by 3% when bloated/duplicated; the
  fix is aggressive dedup, not more rules.
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/grok-build-runtime-docs-divergence
    type: refines
  - target: wiki/concepts/skill-enforcement-layers
    type: related
---

# Context file deduplication: AGENTS.md as source of truth, Claude files as include stubs

## The problem

A host running multiple AI coding tools (Claude Code, Codex CLI, Cursor,
Grok Build) accumulates context files in multiple formats at multiple
layers:

- User-global: `~/.grok/AGENTS.md`, `~/.claude/CLAUDE.md`
- Workspace: `P:\AGENTS.md`, `P:\Claude.md`, `P:\.claude/CLAUDE.md`
- Rules: `P:\.claude/rules/*.md` (10+ files)
- Bundled copies: `~/.grok/bundled/skills/*/` may duplicate user copies

On Grok Build, the compat layer (`compat.claude.rules = true`,
`compat.claude.agents = true`) auto-loads the Claude-format files into
every session's system prompt. The result on this host: ~2400 lines of
context per turn, mostly duplicated across Grok and Claude formats. The
model spends tokens reconciling conflicts between formats and may quote
Claude-specific framing (hook patterns, settings paths) as authoritative
on a host where those don't apply.

## The wrong frame: "toggle the compat layer"

The compat layer is not the problem. Toggling `compat.claude.rules =
false` stops the loading but doesn't fix the underlying duplication —
the rules content still exists in two places, and turning the scanner
off risks silently losing load-bearing rules.

## The right frame: single source of truth per layer

The goal is one canonical content location per layer (user-global,
workspace, rules), regardless of which format each harness discovers.
Once there's one source of truth, the compat layer becomes harmless —
it loads the same content via multiple paths, but the content is
identical, so there's no conflict to reconcile.

## The canonical pattern (verified against official Claude docs)

Per Claude Code's documentation (`code.claude.com/docs/en/memory`) and
the broader cross-tool convention:

- **AGENTS.md is the cross-tool standard.** Codex, Cursor, Copilot, and
  (with the compat layer) Grok Build all read it.
- **CLAUDE.md should be a thin `@AGENTS.md` import + Claude-specific tail.**
  The official docs show this exact pattern:
  ```markdown
  @AGENTS.md

  ## Claude Code-specific
  (anything that only applies to Claude Code, e.g., compaction behavior)
  ```
- **Windows caveat:** symlinks require admin/dev mode, so use the
  `@AGENTS.md` import form rather than `ln -s AGENTS.md CLAUDE.md`.

## What the research says (do's and don'ts)

### ETH Zurich study (Gloaguen et al., Feb 2026)

Paper: "Evaluating AGENTS.md" ([arxiv 2602.11988](https://arxiv.org/abs/2602.11988)).

- **LLM-generated context files reduced task success by 3%** vs no
  context file at all.
- **Human-written files improved success by ~4%** but increased inference
  cost >20%.
- **Length is the dominant failure mode.** Frontier models reliably
  follow ~150-200 instructions; beyond that, they drop rules
  unpredictably.
- **Redundancy with code is the second failure mode.** Restating what's
  in `package.json`, `tsconfig.json`, or `.eslintrc` adds noise without
  value — the agent can read those files.

### The 10 mistakes pattern (termdock, drawing on the ETH study)

1. **Too long** — target <100 lines per file. Every line must pass: "if
   I remove this, will the agent make a mistake it cannot recover from
   by reading the code?"
2. **Restating information the agent can derive** — dependency lists,
   tsconfig flags, lint rules. Delete.
3. **No architecture section** — the one thing the agent can't infer
   quickly from a cold start.
4. **Missing build/test commands** — the highest-ROI content.
5. **Overly rigid ALWAYS/NEVER rules** — use "prefer" with explicit
   exceptions to give the agent judgment space.
6. **No constraints section** — constraints prevent damage; conventions
   are aspirational. Constraints are higher-ROI.
7. **Duplicating linter rules** — the linter is deterministic; CLAUDE.md
   is not. Don't restate what the linter enforces.
8. **Ignoring AGENTS.md cross-tool compatibility** — building
   everything in CLAUDE.md creates tool lock-in.
9. **Not versioning** — CLAUDE.md/AGENTS.md are project docs. Commit them.
10. **Stuffing task workflows that should be skills** — task-specific
    content belongs in SKILL.md (on-demand load), not in always-loaded
    context.

## Strategy menu (in order of preference)

### A1 — Claude files become `@`-include stubs (recommended first move)

Replace `~/.claude/Claude.md`, `P:\Claude.md`, `P:\.claude/CLAUDE.md`
with one-line files: `@~/.grok/AGENTS.md` (or `@AGENTS.md` for the
workspace-level file). The compat layer still loads them, but they're
~1 line each instead of 250-450 lines. Actual content lives in the
Grok files.

- **Pro:** No harness config change. No content loss. ~75% context
  token reduction. Reversible.
- **Con:** Depends on `@`-include being honored by Grok Build's compat
  scanner. Verified for Claude Code; **needs verification for Grok
  Build's compat layer specifically** (the docs say compat.claude
  follows Claude's CLAUDE.md resolution, but include-expansion is an
  implementation detail).
- **Falsifier:** if the compat scanner doesn't expand `@`, the Claude
  files become inert stubs and any rule only in Claude format is lost.

### B1 — Port unique content into AGENTS.md, then replace Claude files with stubs

Audit what's in the Claude files that isn't in the Grok equivalents.
Port the unique parts into AGENTS.md. Then apply A1.

- **Pro:** Cleanest end state. No content loss risk.
- **Con:** Largest effort (audit + port + test).

### B2 — Shared include file, both formats reference it

Move all rules into `~/.shared/rules.md` or `P:/.shared/rules.md`. Both
AGENTS.md and CLAUDE.md point at it. Works for any future harness.

- **Pro:** True single source of truth. Adding a rule means editing one
  file.
- **Con:** New directory convention. Most invasive.

### C1 — Symlinks/junctions

Make `CLAUDE.md` a junction to `AGENTS.md`. Transparent to the harness.

- **Con on Windows:** junctions are fragile (break on copy, on some
  sync tools). Windows symlinks require admin/dev mode. Reject for
  this host.

### D1/D2 — Label the duplication, don't fix it

Add "this is a compat mirror" headers, or add a precedence rule to
AGENTS.md. Doesn't reduce tokens, doesn't prevent drift. Weakest.

## Recommended sequence for this host

1. **Verify `@`-include works under Grok Build compat.** Replace one
   file (e.g., `P:\Claude.md`, currently a 1-line `@AGENTS.md` already)
   with a 2-line version that adds a marker comment. Confirm the marker
   appears in the next session's system-reminder context block.
2. **Apply A1 to all Claude-format files** if step 1 passes.
3. **Run B1 (port unique content) over time** as you audit what's
   actually load-bearing in each Claude file.
4. **Apply the 10-mistakes audit** to the surviving canonical files
   (AGENTS.md at each layer). Target <200 lines per file. Delete
   linter-redundant content. Move task workflows to skills.

## Why this matters beyond token savings

The ETH study's finding that context files can *reduce* success rates is
counterintuitive but structural: every duplicated line competes for
attention with the actual task. On a host like this one, where ~2400
lines of context load every turn, the model is spending real reasoning
capacity reconciling formats and resolving conflicts between Claude and
Grok versions of the same rule. Dedup isn't aesthetic cleanup; it's
correctness engineering.

## Companion anti-patterns

- **Don't toggle `compat.claude.*` to `false` before porting content.**
  Silent rule loss is worse than duplication.
- **Don't use symlinks on Windows for load-bearing config.** Junctions
  break under sync tools and cross-filesystem operations.
- **Don't restate what the linter/tsconfig/package.json already says.**
  That's the second-most-common failure mode in the ETH study.
- **Don't put task workflows in always-loaded context.** Use SKILL.md
  (on-demand load) for procedures; reserve context for architecture,
  constraints, and commands.

## Source

- Research base: ETH Zurich "Evaluating AGENTS.md" (Gloaguen, Mundler,
  Muller, Raychev, Vechev — arxiv 2602.11988, Feb 2026)
- Official Claude Code memory docs: `code.claude.com/docs/en/memory`
- 10-mistakes analysis: `termdock.com/en/blog/claude-md-common-mistakes`
  (Danny Huang, March 2026)
- HN discussion of symlink pattern: `news.ycombinator.com/item?id=45786738`
- Session context: 2026-07-21 session probed the Grok Build compat layer
  (`config.toml` lines 30-33), the auto-load chain in the system
  reminder, and the question of whether `@`-include syntax is honored
  by the compat scanner. Verification of `@`-include under Grok Build
  is pending; the pattern is verified for Claude Code.

## Auto-related

- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
