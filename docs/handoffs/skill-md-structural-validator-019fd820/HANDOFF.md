---
thread_id: skill-md-structural-validator-019fd820
parent_handoff_path: P:/docs/handoffs/batch-skill-defect-cleanup-20260806/HANDOFF.md
current_session_id: 019fd820-2fb5-7330-a0ab-290d5e529658
parent_session: none
current_terminal_id: grok-019fd820
produced_at: 2026-08-07T00:00:00Z
last_updated_by: 019fd820-2fb5-7330-a0ab-290d5e529658
last_updated_at: 2026-08-07T00:00:00Z
status: open
handoff_type: implementation
accurate_as_of_head: HEAD
---

# Handoff: Build SKILL.md structural validator (`skill_validator.py`)

## Objective

Build a Python validator that checks SKILL.md files for structural defects at the frontmatter and content level — complementing the existing `script_scan.py` which only checks `__lib/` Python scripts. Wire it as a pre-commit hook so defects are caught at commit time, not during reactive reviews.

## Motivation (measured)

A 40-line audit script (`P:/tmp/skill_audit.py`) scanned all 72 active Grok-native skills and found **106 structural issues** — an average of 1.5 per skill:

| Defect class | Count | Rate | Example |
|---|---|---|---|
| Missing `version:` field | 49 | 68% | Most skills have no version tracking |
| Missing `host:` field | 21 | 29% | Cannot determine Grok vs Claude applicability |
| Over 500 lines | 12 | 17% | `tp` (1662), `design` (1444), `model-web` (1350), `www` (1260) |

Additionally, this session produced 2 description-body consistency errors:
- ERROR-1: `/insight` description claimed "9 categories" but listed 8 in the parenthetical
- ERROR-5: `/close` referenced "6-category scan" when the source had evolved to 9

These errors were caught reactively (architecture review), not at write time — a structural validator would have caught them at commit.

## Relationship to existing work

| Existing tool | What it checks | What it misses |
|---|---|---|
| `script_scan.py` (`/skill-dev`) | `__lib/` Python scripts: AST-level code defects | SKILL.md frontmatter, content structure, description-body consistency |
| `propagation_check.ps1` | References to renamed/deleted skills | Doesn't run automatically — manual invocation |
| `validate_wiki_entry.py` (`/wiki`) | Wiki concept structure (frontmatter, sections, cross-refs) | Only for wiki concepts, not skills |
| `quality_gates_frontmatter.py` | Quality-gate frontmatter declarations | Only checks `quality_gates` field, not general frontmatter |

This validator fills the gap: SKILL.md-level structural checks that run at commit time.

## External tool research (rule specifications, not implementations)

Two external tools provide the *rule list* to draw from:

1. **skill-linter** (aicatalyst-team/skill-linter) — 47 rules across 5 categories (structural, frontmatter, content, security, best practices). Node.js. Follows the Agent Skills spec (6 allowed frontmatter fields). Good rule taxonomy; wrong ecosystem (Node) and wrong schema (their spec has 6 fields, ours has 12+).

2. **ai-linter** (fchastanet/ai-linter) — Python, pip-installable, pre-commit integration. Validates frontmatter, content length, token count, file references. Checks for unreferenced resource files. Closer to our stack.

3. **agent-gates** (zl190/agent-gates) — structural vs semantic gate distinction. Structural = "does a diagnosis exist?" (free, fast). Semantic = "does the diagnosis identify a root cause?" (costs tokens). The validator should be structural only.

4. **hivelore** (Doucs91/hivelore) — "capture a mistake → attach a validated guard → the commit that repeats it is refused." The pattern of turning documented lessons into deterministic gates is directly applicable: wiki concepts documenting failure modes could carry sensor patterns that block re-introduction.

## Scope

### In scope

- `skill_validator.py` — Python script at `~/.grok/skills/skill-dev/__lib/` (alongside `script_scan.py`)
- Checks SKILL.md files (not `__lib/` scripts — that's `script_scan.py`'s job)
- Pre-commit hook for `~/.grok/skills/` and `P:/.agents/skills/`

### Out of scope

- Fixing the 106 existing defects (that's `batch-skill-defect-cleanup-20260806`)
- Semantic checks (description quality, instruction clarity — those need LLM judgment)
- `__lib/` Python code checks (that's `script_scan.py`)
- Wiki concept validation (that's `validate_wiki_entry.py`)

## Rule set (workspace-specific)

### Frontmatter rules (from our schema)

| Rule | Severity | What it checks |
|---|---|---|
| `name-required` | error | `name:` field exists in frontmatter |
| `name-matches-directory` | error | Name field matches parent directory name |
| `description-required` | error | `description:` field exists |
| `description-min-length` | warning | Description is substantive (≥50 chars) |
| `host-required` | warning | `host:` field exists (grok, claude, or both) |
| `version-required` | info | `version:` field exists |
| `depends-on-valid` | warning | Each skill in `depends_on:` resolves to an existing skill |
| `provides-nonempty` | info | `provides:` field is non-empty |
| `techniques-present` | info | `techniques:` field exists (workspace convention) |

### Content rules

| Rule | Severity | What it checks |
|---|---|---|
| `body-not-empty` | error | SKILL.md has content below frontmatter |
| `line-limit` | warning | Body ≤500 lines (flag bloat, not block) |
| `no-backslash-paths` | info | Use forward slashes (Windows/Python safety) |
| `file-references-valid` | warning | Paths referenced in code blocks resolve |

### Description-body consistency rules (the session's error class)

| Rule | Severity | What it checks |
|---|---|---|
| `category-count-match` | warning | If description claims "N categories/modes/types," the parenthetical lists exactly N items |
| `capability-claim-traceable` | info | If frontmatter `provides:` lists capabilities, the body references them |

### Security rules (from skill-linter's Snyk/OWASP set)

| Rule | Severity | What it checks |
|---|---|---|
| `no-prompt-injection` | error | Detects prompt injection patterns (context-aware — quoted/code-block patterns downgraded) |
| `no-credential-access` | error | Detects sensitive file/env access patterns |
| `no-curl-bash` | error | Detects pipe-to-shell execution patterns |

## Acceptance criteria

1. `skill_validator.py` exists at `~/.grok/skills/skill-dev/__lib/`
2. Running `python skill_validator.py <skill-path>` checks all rules above
3. Exit code 0 = pass, 1 = errors found, 2 = warnings only
4. `--json` output mode for CI/programmatic consumption
5. Pre-commit hook installed for `~/.grok/skills/` and `P:/.agents/skills/`
6. Running it against `/insight` catches ERROR-1 (category count mismatch) — this is the falsifier
7. Integration with `script_scan.py`: both can run from the same pre-commit invocation

## Falsifier

This validator is wrong if:
- The category-count-match rule has a high false-positive rate (many skills use "N" loosely without listing items)
- The security rules produce noise on skills that legitimately reference credential patterns (e.g., `/recover` skill)
- The pre-commit hook adds >2 seconds to commit time (developers will bypass it with `--no-verify`)

## Resumption protocol

1. Read `P:/tmp/skill_audit.py` — the 40-line prototype that found 106 issues
2. Read `~/.grok/skills/skill-dev/__lib/script_scan.py` — the existing code-level scanner to extend alongside
3. Read the skill-linter rule set (https://github.com/aicatalyst-team/skill-linter) for the full 47-rule taxonomy
4. Build `skill_validator.py` with the rule set above
5. Wire as pre-commit hook
6. Test against `/insight` (should catch ERROR-1) and `/tp` (should flag line-limit)

## Suggested next invocation

```
/go build skill_validator.py — SKILL.md structural validator with frontmatter, content,
and description-body consistency rules, wired as pre-commit hook for skill directories
```

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-07 | 019fd820 | created |
