---
title: "Disabling Claude compat instruction loading — instruction budget decision"
created: 2026-07-28
source: session-019fa48a (AGENTS.md refactor)
tags: [agents-md, instruction-budget, compat, config, decision, grok-build]
host: grok
agent: grok
verification: observed
cognitive_load: 2
summary: >
  Set compat.claude.agents = false in config.toml to stop loading 3 Claude-format
  instruction files (~583 lines) that were triplicating rules already in the Grok
  instruction files. Reduced total loaded instruction budget from ~1,679 lines to
  ~620 lines (63% reduction). The skills, rules (permission deny), and mcps compat
  flags remain ON — only the instruction file loading (agents) was cut. One unique
  rule (replacement default) was ported before flipping the switch.
relations:
  - target: wiki/concepts/agents-md-construction-best-practices.md
    type: extends
  - target: wiki/concepts/enforcement-hierarchy-and-compaction-strategy.md
    type: related
---

# Disabling Claude compat instruction loading

## Decision context

**The problem:** Grok Build loaded 4 instruction files every turn — `~/.grok/AGENTS.md` (1,170 lines), `P:\AGENTS.md` (602 lines), `~/.claude/Claude.md` (358 lines), `P:\.claude\CLAUDE.md` (220 lines), `P:\CLAUDE.md` (5 lines). Total: ~1,679 lines (~90KB). This exceeded the ~150-200 instruction ceiling documented in [[agents-md-construction-best-practices]].

**The question:** can we stop loading the Claude files entirely, since we have Grok-native equivalents?

## The decision

Set `compat.claude.agents = false` in `~/.grok/config.toml`:

```toml
[compat.claude]
hooks = false      # already off — Claude hooks don't fire on Grok Build
skills = true      # keep — Claude skill discovery still useful
rules = true       # keep — permission deny rules from settings.json
agents = false     # CHANGED — stops loading CLAUDE.md files
mcps = true        # keep — MCP server config from ~/.claude.json
```

Same for `[compat.cursor]`: `agents = false`.

## What this eliminated

| File | Lines | Content |
|------|-------|---------|
| `~/.claude/Claude.md` | 358 | Global Claude preferences (identity, platform conventions, safety rules) |
| `P:/.claude/CLAUDE.md` | 220 | Claude constitution v9.0 (philosophy, operating principles, hook reference) |
| `P:/CLAUDE.md` | 5 | Just `@AGENTS.md` include |

## What was preserved

Before flipping the switch, high-value unique rules from the Claude files were ported into `~/.grok/AGENTS.md`:
- **Replacement default** (delete X when replacing with Y)
- All other content was either duplicated (edit-then-verify, destructive git, claim verification) or Claude-Code-specific (TaskCreate schema, Plugin Mutation Checklist, `__lib` naming)

## Steelman of the rejected alternative (keep agents=true)

The argument for keeping the Claude files loaded: defense in depth. Even if the rules are duplicated, having them in multiple files means a single-file edit failure doesn't lose the rule. Also, some Claude-specific conventions (pyproject.toml structure, plugin.json format) might matter when working on Claude marketplace packages.

**Why rejected:** the duplication costs more than it protects. 583 lines of triplicated rules degrade instruction-following on ALL rules uniformly (per HumanLayer research, documented in [[agents-md-construction-best-practices]]). The Claude-specific conventions are only relevant when editing `P:\packages\.claude-marketplace\` — and those packages have their own `CLAUDE.md` files that can be read on demand. The enforcement hierarchy in [[enforcement-hierarchy-and-compaction-strategy]] clarifies that duplicated prompt instructions are the weakest enforcement form — better to have one canonical copy than three degraded copies.

## Result

| Metric | Before | After |
|--------|--------|-------|
| Files loaded | 4 (+1 include) | 2 |
| Total lines | ~1,679 | ~620 |
| Total bytes | ~90KB | ~37KB |
| Reduction | — | 63% |

## Why instruction budget matters more than defense-in-depth

The HumanLayer research (documented in [[agents-md-construction-best-practices]]) shows that instruction-following quality degrades **uniformly** as instruction count increases — the model doesn't ignore newer instructions specifically; it degrades on ALL of them. This means triplicated rules (edit-then-verify in 3 files) don't produce 3× enforcement; they produce ~0.7× enforcement per copy because each copy is weaker due to budget pressure.

The ETH Zurich study (arXiv:2602.11988) found that LLM-generated instruction files net -3% success rate — meaning a non-trivial fraction of typical content is *actively harmful*. The Claude compat files were never curated for Grok Build — they were Claude Code artifacts loaded by a compatibility layer. Loading uncurated content into the instruction budget is worse than loading nothing.

## What was NOT lost

The permission deny rules (in `~/.claude/settings.json`) still fire because `compat.claude.rules = true`. Skill discovery from `~/.claude/skills/` still works because `compat.claude.skills = true`. MCP servers from `~/.claude.json` still connect because `compat.claude.mcps = true`. Only the instruction file loading (`agents`) was cut. The Claude files still exist on disk and can be read on demand — they're just not force-loaded into every turn's context.

## What this means for our workspace

The instruction budget is now controlled entirely by two files: `~/.grok/AGENTS.md` (global behavioral rules) and `P:\AGENTS.md` (workspace-specific rules). Any new rule must go into one of these two files or into a hook (for mechanical enforcement). There is no third compat file to accidentally duplicate into. The backout path is simple: `agents = true` restores the Claude files on next restart. The backup files (`AGENTS.md.backup-20260728` at both paths) exist for comparison if questions arise about what was removed.

This decision should be revisited if Grok Build adds native support for prioritized instruction loading (where some files are marked "high priority" and others "background"). Until then, the binary on/off switch is the right granularity.

## Falsifier

This is wrong if: (a) a rule that was only in the Claude files becomes needed and wasn't ported, or (b) working on Claude marketplace packages requires the Claude conventions at inference time (test by editing a plugin and checking whether conventions are followed). Backout: set `agents = true` — takes effect on next session restart.

## Receipts

- `~/.grok/config.toml:60-65` — `[compat.claude] agents = false` (the config change)
- `~/.grok/config.toml:67-72` — `[compat.cursor] agents = false` (same change for Cursor)
- `~/.grok/docs/user-guide/05-configuration.md:344-349` — documents what `agents` flag controls (`scan ~/.claude/ and <dir>/.claude/CLAUDE*.md`)
- `~/.grok/active-surface.last.md:11-20` — confirms `claude.agents: OFF` after restart
