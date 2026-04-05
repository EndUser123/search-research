---
name: gto
version: 3.6.0
status: "stable"
description: Gap/Task/Opportunity analysis with self-verifying completion enforcement and first-class contract-authority gap detection
category: analysis
enforcement: strict
triggers:
  - /gto
  - "gap analysis"
  - "health check"
  - "analyze project state"
---

# GTO v3.1 - Gap/Task/Opportunity Analysis

Chat-based gap detection for technical projects with self-verifying completion enforcement.

## What It Does

GTO analyzes your codebase to identify gaps, tasks, and opportunities across:
- Missing test coverage
- Documentation gaps
- Code quality issues (TODO, FIXME, etc.)
- Dependency health
- Project health metrics
- Contract gaps (producer/consumer mismatches, implied schemas, stale-data risks)
- **Chat history patterns** (recurrent issues, cleanup opportunities)

## Completeness Target (v3.x)

"Complete" for GTO v3.x means:

| Layer | Criterion | Target |
|-------|-----------|--------|
| L1 detectors | All 7 detector types produce output | 100% |
| L1 detectors | No false-positive spikes (>20% of lines flagged as TODO with no real TODOs) | 0 regressions |
| L2 subagent | GapFinderSubagent produces categorized gaps | 100% |
| L2 subagent | No silent failures (unhandled exceptions) | 0 in last 10 runs |
| Output | Health score 0-100% reported | 100% |
| Output | Gap list non-empty (or explicit "no gaps" signal) | 100% |
| Self-verification | gto_assertions.py A1-A5 all pass | 100% |
| Persistence | State file written, readable on next run | 100% |

Scores are measured against this table. A "complete" run is one where all rows are green.
A "partially complete" run is one where 1-2 rows fail. A "failed" run is 3+ failures or a critical (A1/A5) failure.

## Usage

```
/gto
```

GTO auto-detects the target from session context via semantic intent resolution:

1. **Named outputs** (highest priority): If user references a named output from conversation (e.g., "gto on the hook system") → use that
2. **Skill invocation target**: Explicit target from skill args (e.g., `/gto on hooks`)
3. **Active task context**: If `/code` or `/planning` was recently running → the feature/plan they were analyzing
4. **Handoff/RESTORE_CONTEXT**: Stated target from transcript_path links
5. **Recent evidence files**: The system described by the artifact — semantic match, not just recency
6. **Conversation context** (last resort): What was the user working on when GTO was invoked? Weight by intent over timestamps

## EXECUTE

**Run GTO analysis via CLI:**

```bash
python P:/.claude/skills/gto/gto_orchestrator.py --format both
```

**What happens:**
- GTO auto-detects the target from session context
- Runs all Layer 1 detectors (tests, docs, dependencies, code markers)
- Optionally runs Layer 2 AI subagents for gap finding
- Produces health score and categorized gap list
- Saves JSON artifact to `.evidence/gto-outputs/`

**Output formats:**
- `--format json`: Saves JSON artifact to `.evidence/gto-outputs/gto-artifact-{timestamp}.json`
- `--format markdown`: Prints markdown to stdout (no file saved)
- `--format both`: Saves JSON to file AND prints markdown to stdout

## Output

GTO produces:
1. Health score (0-100%) across 4 dimensions
2. Categorized gap list (testing, docs, dependencies, code_quality, contracts)
3. Recommended next steps with effort estimates
4. JSON artifact for tool integration
5. **History insights** (from session transcript analysis)

## Architecture

Three-layer design:
- **Layer 1**: Python deterministic detectors (fast, reliable)
- **Layer 2**: AI subagents (gap finding with line numbers) + Gap-to-Skill Mapper
- **Layer 3**: Claude orchestrator (coordination and formatting)

### Gap-to-Skill Mapping (Layer 2)

GTO includes an intelligent skill recommendation system that analyzes gaps and suggests relevant skills:

**Components:**
- `lib/skill_registry_bridge.py` - Loads skill metadata from registry with fallback catalog
- `lib/gap_skill_mapper.py` - Maps gap types to skill categories using `GAP_TYPE_TO_CATEGORIES`
- `lib/skill_coverage_detector.py` - Gap-aware recommendations for RSN output

**How it works:**
1. When gaps are found, GTO analyzes each gap's type (test_gap, doc_gap, etc.)
2. Gap types are mapped to relevant skill categories (testing, documentation, quality, etc.)
3. Skills are matched based on category, domain, and trigger keywords
4. Recommendations include skill descriptions and rationale

**Gap Type → Skill Category Mapping:**

| Gap Type | Categories | Example Skills |
|----------|------------|----------------|
| test_gap, test_failure | testing, quality | /tdd, /qa, /critique |
| doc_gap, missing_docs | documentation | /doc, /docs, /docs-validate |
| code_quality, design_issue | quality, review | /critique, /uci |
| import_issue, dependency | dependencies | /deps, /verify |
| contract_gap, stale_data_risk, consumer_gap | architecture, verification, state | /arch, /planning, /verify |
| git_dirty, uncommitted | vcs, git | /git, /push |
| runtime_error, bug | debugging | /debugRCA, /diagnose |

**LLM Context Injection:**
When generating recommendations, GTO injects skill context into the RSN output so the LLM understands what skills are available and what they do. This enables context-aware suggestions rather than static recommendations.

## Multi-Terminal Safety

Each terminal gets isolated state:
- State directory: `.evidence/gto-state-{terminal_id}/`
- No shared mutable state between terminals
- Atomic writes prevent corruption

## Contract Gap Detection

GTO should detect producer/consumer gaps as a first-class output category.

Examples:

- artifact written but no consumer found
- consumer reads fields never guaranteed by producer
- implied schema exists only in prose/comments
- contract-sensitive boundary exists but no `Contract Authority Packet` exists
- packet exists but downstream work ignores or contradicts it
- no freshness/invalidation rule
- no validator on resume/handoff payload
- stale summary is treated as source of truth over transcript/workspace state

## Routing Behavior

`/gto` should suggest the owning lower skill for each gap family:

- `/arch` for state, contract, identity, ordering, dedupe, invalidation, or stale-data gaps
- `/planning` for execution-shape or missing contract-boundary matrix gaps
- `/verify` for unproven behavior or missing boundary-proof gaps
- `/critique` for adversarial review of risky or blind-spot-heavy changes
- `/pre-mortem` for risky fixes, recurring failures, or low-reversibility changes

`/gto` identifies and routes. It does not directly absorb those responsibilities.

## Skill Coverage Log

GTO maintains an append-only log of skill executions per target for routing suggestions.

**Location:** `.evidence/skill_coverage/{target_key}.jsonl`

**Format (one JSON object per line):**
```json
{"skill": "/critique", "target": "skills/usm", "terminal_id": "console_abc123", "timestamp": "2026-03-24T...", "git_sha": "abc1234"}
```

**Key properties:**
- **Append-only**: New entries are always added, never modified
- **Per-target isolation**: Each project/folder gets its own log file
- **No TTL**: Freshness determined by git state — if target changed since last run, coverage is stale
- **Auto-rotation**: Log rotates when >1MB (keeps last 100 entries)

**How it works:**
1. When gaps=0, GTO reads the skill coverage log for the target
2. Checks git state to detect staleness (file changed since skill run)
3. Classifies project type and suggests relevant skills that haven't been run
4. Suggestions appear as RSN findings with `action_type: "Use /skill"`

**Reference:** `lib/skill_coverage_detector.py` — `detect_skill_coverage()` function

## Verification (MANUAL)

**Before claiming "done", you MUST:**

1. Run the binary assertions script:
   ```
   python P:/.claude/skills/gto/evals/gto_assertions.py
   ```
   **Note:** Terminal ID is auto-detected from environment variables (`CLAUDE_TERMINAL_ID`, `TERMINAL_ID`, etc.) or derived from PID+timestamp.

2. Paste the full output showing all assertions passed

3. Only claim "done" if ALL assertions pass (exit code 0, score 100/100)

**If any assertion fails:**
- Diagnose the failure from the assertion output
- Fix the issue (missing artifacts, failed checks, etc.)
- Re-run assertions until all pass
- THEN claim "done"

## Binary Assertions

The assertions script checks 5 criteria:

- **A1**: Artifacts exist (gapfinder, health, or gitcontext files created in last hour)
- **A2**: Health score reported (0-100% in artifact files)
- **A3**: Viability check passed (no FAIL status in viability artifacts)
- **A4**: Git repository valid (.git directory exists)
- **A5**: State directory accessible

## Reference

See `references/` directory for:
- `architecture.md` - Full system architecture
- `api.md` - Complete API reference

**Hook Path Resolution**: GTO skill hooks use relative paths (`../skills/gto/hooks/`) not absolute paths. See `memory/skill_hooks_path_resolution.md` for details on skill-based hook path resolution.

## Recommended Next Steps (RNS)

GTO uses a **dynamic RNS format** that groups findings by category, following the critique RNS pattern but with dynamically-generated domains based on gap types detected.

### Dynamic Domain Categories

The formatter automatically groups gaps into categories based on type:

| Gap Type | Domain | Examples |
|----------|--------|----------|
| `test_failure`, `missing_test` | tests | Failing tests, missing test files |
| `missing_docs`, `outdated_docs` | docs | Missing documentation, outdated docs |
| `git_dirty`, `uncommitted_changes` | git | Uncommitted changes, dirty state |
| `import_error`, `missing_dependency` | dependencies | Import errors, missing packages |
| `code_quality`, `tech_debt` | code_quality | TODO/FIXME, code smells |
| `contract_gap`, `consumer_gap`, `stale_data_risk` | contracts | Missing validators, implied fields, stale-artifact reuse |

### Output Format

🧪 TESTS
  TEST-001 [~5min] [R:1.25] Fix missing test in test_file.py (file:45)

📄 DOCS
  DOC-001 [~15min] [R:1.0] Add docstring to function_x (src/utils.py:78)

🔧 QUALITY
  QUAL-001 [~30min] [R:1.75] Refactor session_manager.py (src/session_manager.py:12)

🐙 GIT
  GIT-001 [~2min] [R:1.0] Commit 3 uncommitted changes in hooks/

📦 DEPS
  DEPS-001 [~5min] [R:1.5] Install missing httpx dependency

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

0 — Do ALL Recommended Next Actions (7 items, ~67min total)

**Format rules:**
- Domain sections use emoji headers (🧪 TESTS, 📄 DOCS, etc.) — no markdown fences
- Items use flat global IDs (TEST-001, DOC-001, not hierarchical 1.1, 1.2)
- Each item shows: `[ID] [~effort] [R:reversibility] Description (file:line)`
- Dependency annotations inline: `[causes: ID]`, `[caused-by: ID]`, `[blocks: ID]`
- Priority within domain: critical → high → medium → low
- Ends with `0 — Do ALL Recommended Next Actions` directive

### Why Dynamic Domains?

Static RNS sections assume all gap types are always present. GTO detects **which gap types actually exist** in the target project and only generates domains for those types. This prevents empty sections and keeps output focused.

### Prioritization: Use Reversibility

When ranking gaps to fix, apply the Reversibility Scale:

| Score | Action |
|-------|--------|
| 1.0–1.25 (Trivial) | Fix immediately |
| 1.5 (Moderate) | Fix with tests |
| 1.75+ (Hard/Irreversible) | Defer unless critical |

**Reference:**
- `lib/next_steps_formatter.py` — `NextStepsFormatter` class
- `memory/reversibility_scale.md` — Reversibility Scale for decision guidance

## Version

3.6.0 (2026-04-02) - Added Contract Authority Packet gap detection and downstream-consumption checks
3.5.0 (2026-04-02) - Added first-class contract gap detection and routing
3.4.0 (2026-04-01) - Remove --project-root override; rely on session context auto-detection
3.3.0 (2026-03-25) - Intelligent gap-aware skill recommendations with LLM context injection
3.2.0 (2026-03-24) - Added skill coverage append-only log with git-state freshness
3.1.0 (2026-03-22) - Added self-verifying infrastructure with binary assertions
