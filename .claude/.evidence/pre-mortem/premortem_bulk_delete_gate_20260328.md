# Pre-Mortem: Bulk Delete Gate Fix (v1.0)

**Target:** `P:\.claude\hooks\PreToolUse_bulk_delete_gate.py`
**Changes:** Inline bypass detection + `.backup` safe pattern
**Date:** 2026-03-28

## Step 1: Failure Scenario

"It's 6 months later. The bulk delete gate fix FAILED — either users lost data due to over-permissive bypass, or the gate still blocks legitimate deletions causing workflow friction."

## Step 2: Failure Causes Analysis (12 + 4 from adversarial review)

### Confirmed by Multiple Agents (HIGH confidence)

1. **Bypass injection via echo/comment** — `re.search(r"\bBULK_DELETE_BYPASS\s*=\s*1\b", command)` matches in echo strings, comments, heredocs. `echo "BULK_DELETE_BYPASS=1" && rm -rf /important/` bypasses gate. (ALL 8 agents)
2. **Stale env var silently disables gate** — `BULK_DELETE_BYPASS=1` in parent env persists across sessions. (6 agents)
3. **Over-broad `.backup` pattern** — `r"\.backup\b"` matches `code.backup.py`, and `project.backup/`. Non-dot-prefixed backup dirs with source files bypasses gate. (5 agents)
4. **LLM learns bypass from block message** — Block message line 241 literally teaches bypass string to LLM. (5 agents)
5. **`.env` file treated as safe** — `r"\benv\b"` matches `.env` secrets files. (2 agents: quality, security)
6. **Recovery tag false confidence** — Tags capture committed state only; uncommitted files lost. Recovery command uses absolute path that fails. (2 agents: QA, logic)

### Additional Findings (MEDIUM confidence)
7. **No audit logging of bypass events** — When bypass fires, no record. (5 agents)
8. **Threshold boundary untested** — Exactly 5 and 6 files counts untested. (1 agent: testing)
9. **Git tag microseconds precision** — `%Y%m%d_%H%M%S` could collide across terminals. (2 agents)
10. **Performance: rglob on 37K+ file directory exceeds 5s timeout** — `count_files()` uses `rglob("*") which can take 5.6s on large directories, exceeding default hook timeout. (1 agent: performance)
11. **`re.match` proposed fix has edge cases** — `BULK_DELETE_BYPASS=1;rm` and `BULK_DELETE_BYPASS=1&&` fail with proposed `re.match` fix. (2 agents: compliance, logic)
12. **`\bbuild\b`, `\bdist\b` over-broad** — Match `src/build_tools/` as safe. (1 agent: logic)

## Step 3: Risk Rating (calibrated by adversarial review)

| # | Agent Consensus | Original Score | Calibrated Score | Action |
|-----|----------------|----------------|--------------------|-------------------|--------|
| 1 | 8/8 CRITICAL | 6 (HIGH) | 9 (CRITICAL) | Fix regex |
| 2 | 6/8 CRITICAL | 4 (MEDIUM) | 9 (CRITICAL) | Narrow .backup pattern |
| 3 | 6/8 HIGH | 6 (HIGH) | 6 (HIGH) | Remove from block message |
| 4 | 5/8 HIGH | 2 (LOW) | 6 (HIGH) | Fix `\benv\b` pattern |
| 5 | 5/8 MEDIUM | 4 (MEDIUM) | 6 (HIGH) | Fix recovery mechanism |
| 6 | 5/8 MEDIUM | 2 (LOW) | 4 (MEDIUM) | Add audit logging |
| 7 | 1/8 LOW | 2 (LOW) | 2 (LOW) | Add boundary tests |
| 8 | 2/8 LOW | 1 (LOW) | 2 (LOW) | Add microseconds |
| 9 | 1/8 CRITICAL (not identified) | N/A | 9 (CRITICAL) | Fix rglob perf |
| 10 | 2/8 MEDIUM | 2 (LOW) | 4 (MEDIUM) | Fix re.match edge cases |
| 11 | 1/8 LOW | 2 (LOW) | 2 (LOW) | Add inclusion criteria |
| 12 | 1/8 LOW | 2 (LOW) | 2 (LOW) | Use path-segment boundaries |

## Step 5: Top 3 Prevention Actions

**P1: Fix bypass regex** (CRITICAL,9)
- Change `re.search` to `re.match` anchored at command start
- Handle edge cases: semicol,, `&&`, multi-var prefix

**P2: Narrow `.backup` safe pattern** (CRITICAL,9)
- Change from `r"\.backup\b"` to `r"(/|^)\.backup(/|$)"`
- Only match dot-prefixed hidden `.backup` directories

**P3: Remove bypass from LLM-visible block message** (HIGH,6)
- Remove line 241 ("Set BULK_DELETE_BYPASS=1 in environment")
- Keep alternatives: delete in smaller batches, verify migration complete
- Bypass mechanism stays in source code only (not LLM-visible output)

## Step 6: Warning Signs

- Bulk delete gate allows >5 rm -rf in single session without blocks
- `pre-delete-*` git tags stop appearing
- `.backup` pattern matches non-backup paths (check logs)

## Step 7: Adversarial Validation Summary

8 agents dispatched in parallel:
- **Compliance**: Bypass regex false positives, bypass in block message (COMP-001, COMP-002)
- **Logic**: Bypass regex edge cases, `.backup` over-broad, `build/dist/env` over-broad (LOGIC-001 through LOGIC-004)
- **Performance**: rglob on 37K files directory exceeds 5s hook timeout (CRITICAL)
- **Security**: 5 findings including bypass injection, .backup over-broad, stale env var, no audit trail, LLM context leakage (SEC-001 through SEC-005)
- **Testing**: 8 findings including missing false positive tests, threshold boundary gaps, mocked create_git_tag (TEST-001 through TEST-008)
- **Quality**: 9 findings including .env false safe, quoted bypass values, stale env var (QUAL-001 through QUAL-009)
- **QA**: 7 findings including recovery tag false confidence, bypass in block message (QA-001 through QA-007)
- **Critic**: Risk #1 under-rated (should be CRITICAL not HIGH), `.backup` blind spot, cascade amplification (CAL-1, BS-1)

**Consensus**: All agents agree bypass regex (line 195) is CRITICAL. Fix: anchor to command start. All agents agree `.backup` pattern is over-broad. Fix: restrict to dot-prefixed directories only.

## Evidence Artifacts

Detailed agent findings:
- `P:/.claude/.evidence/pre-mortem/compliance-findings.json` (7 findings)
- `P:/.claude/.evidence/pre-mortem/logic-findings.json` (7 findings)
- `P:/.claude/.evidence/pre-mortem/performance-findings.json` (6 findings)

## Testing & Watchlist (Operational Checklist)

**Per run**
- [ ] Verify bypass regex no longer matches echo/comment strings
- [ ] Verify `.backup` only matches dot-prefixed hidden directories
- [ ] Verify `.env` files are NOT treated as safe

**Cadence**
- [ ] Monitor git tag creation success rate
- [ ] Review safe pattern list for scope creep quarterly
