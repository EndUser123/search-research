# /refactor + /code-review Integration Analysis

## Investigation Findings

### What `/refactor` Currently Does
- **10-agent discovery** with staggered launches (30s apart)
- Uses `adversarial-io-validation` for TOCTOU/I/O issues
- **16-step workflow**: DISCOVER → DEDUPLICATE → EVIDENCE_VERIFY → PLAN → RED → REFACTOR → VALIDATE
- **Graceful degradation**: Skips timed-out agents

### What `/code-review` Currently Does
- **4 specialist agents** launched in parallel:
  - `adversarial-security`
  - `adversarial-logic`
  - `adversarial-performance`
  - `adversarial-quality`
- **Health Score**: 100 - (CRITICAL×20 + HIGH×10 + MEDIUM×5 + LOW×2)
- **Synthesis**: Combines findings into actionable report

### Why `/code-review` Found Issues `/refactor` Missed

**HYPOTHESIS 1 (Most Likely): Agent Timeout/Skip**
- `/refactor` staggers agents 30s apart; with 10 agents, later agents run 4.5 minutes after start
- If `adversarial-io-validation` was agent #10, it may have timed out or been skipped
- **Evidence**: No refactor findings artifacts exist for `/chs export` run

**HYPOTHESIS 2: Meta-Critique Filtering**
- `/refactor` has Phase 2 meta-critique that "catches false positives before they reach the user"
- Aggressive filtering may have suppressed legitimate CRITICAL findings
- **Evidence Needed**: Check meta-critique logs from `/chs export` run

**HYPOTHESIS 3: Prompt Specificity**
- `/code-review` agents use focused adversarial prompts from `__lib/adversarial_review_protocol.md`
- `/refactor` agents use 10-dimension rubric which may dilute focus
- **Evidence Needed**: Compare actual agent prompts side-by-side

## The Gaps

| Issue | `/refactor` Coverage | `/code-review` Coverage |
|-------|---------------------|-------------------------|
| TOCTOU race conditions | ✅ `adversarial-io-validation` | ✅ `adversarial-logic` |
| O(N²) memory patterns | ❌ Not in agent configs | ✅ `adversarial-performance` |
| Hardcoded paths | ✅ `adversarial-quality` | ✅ `adversarial-quality` |
| Path traversal | ✅ `adversarial-io-validation` | ✅ `adversarial-security` |
| Health Score | ❌ No scoring | ✅ 100-point score |
| I/O validation | ✅ Dedicated agent | ✅ Covered by Logic/Security |

## Design: `/refactor` as Superior Superset

### Option 1: Add `/code-review` Phase to `/refactor` Workflow
Insert `/code-review` between **EVIDENCE_VERIFY** and **PLAN**:
```
DISCOVER → DEDUPLICATE → EVIDENCE_VERIFY → CODE_REVIEW → PLAN → RED → ...
```

**Pros**:
- Minimal changes to existing workflow
- `/code-review` becomes gatekeeper for CRITICAL findings
- Health Score provides quality metric

**Cons**:
- Duplicate analysis (both do discovery)
- Longer workflow (4 more agents)
- Risk of conflicting findings

### Option 2: Merge `/code-review` Agents into `/refactor` Discovery
Replace overlapping `/refactor` agents with `/code-review` specialists:
```
Current /refactor:     adversarial-bugs, adversarial-performance (×2), adversarial-quality, adversarial-security, adversarial-io-validation
Proposed /refactor:    adversarial-security, adversarial-logic, adversarial-performance, adversarial-quality, adversarial-io-validation
```

**Pros**:
- Single discovery phase
- No duplicate work
- Inherits Health Score calculation
- Cleaner agent set (5 vs 10)

**Cons**:
- Loses some specialized agents (python-simplifier, /ai-pi agents)
- May need to re-tune agent prompts

### Option 3: Hybrid - `/code-review` as Optional Deep Dive
Add `--deep-review` flag to `/refactor`:
```
/refactor <path>           # Standard 10-agent workflow
/refactor <path> --deep    # 10-agent + 4-agent code-review synthesis
```

**Pros**:
- Backward compatible
- User control over depth
- Best of both worlds

**Cons**:
- More complex CLI
- Two workflows to maintain

## Recommendation: Option 2 (Merge with Health Score)

**Rationale**:
1. `/refactor`'s current 10-agent set has overlap and redundancy
2. `/code-review`'s 4 agents cover 90% of `/refactor`'s concerns
3. Health Score provides missing quality metric
4. Simpler = more reliable (fewer timeout points)

**Implementation**:
1. Replace `/refactor` agent list with `/code-review` specialists + `adversarial-io-validation`
2. Add Health Score calculation to PLAN output
3. Keep `/code-review` as standalone for quick reviews
4. Update agent-configs.md with new 5-agent set

**Agent Mapping**:
```
Old /refactor → New /refactor
adversarial-bugs → adversarial-logic
adversarial-performance (DRY) → adversarial-quality
adversarial-performance (perf) → adversarial-performance
adversarial-quality → (keep)
adversarial-security → (keep)
adversarial-io-validation → (keep)
python-simplifier → DROP (handle in quality)
/ai-pi agents → DROP (can invoke manually if needed)
adversarial-performance (×2) → SINGLE adversarial-performance
```

**Rollback Plan**: Keep agent-configs.md.old, feature flag via `--legacy-agents`

## Next Steps

1. Update `/refactor/references/agent-configs.md` with 5-agent set
2. Add Health Score calculation to `refactor_plan.py`
3. Test on `/chs export` to verify CRITICAL issues now caught
4. Fix artifacts path: `P:/packages/X/.claude/.artifacts/` → `P:/.claude/.artifacts/{terminal_id}/`
