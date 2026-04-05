# ADR-20260317: Subprocess-Based Adversarial Runner

**Status:** Proposed | Accepted | Superseded by ADR-YYYYMMDD
**Date:** 2026-03-17
**Context:** Context exhaustion during plan-workflow adversarial review when Agent tool delivers all agent responses to parent context

---

## Decision

Replace Agent tool-based adversarial review invocation with subprocess-based runner that writes agent outputs to terminal-scoped state files and returns only a compact summary to context.

---

## Rationale

### Problem Statement

The current plan-workflow skill uses the Agent tool to launch 8 adversarial agents in parallel. Each agent's full JSON response (~2-5KB) is delivered to the parent context, totaling ~14-35KB of tokens. This causes context exhaustion before auto-compact can trigger.

### Root Cause

The Agent tool is designed for **conversational multi-agent workflows**, not **high-volume parallel processing**. By design, it:
- Delivers all agent responses to parent context
- Provides no control over what enters context
- Supports interactive dialogue (not file-first architecture)

### Solution Architecture

File-first, context-second pattern:
1. Agents run as subprocess scripts
2. Outputs written to terminal-scoped state files
3. Only compact summary JSON enters context
4. On-demand detailed access via file reading

### Multi-Terminal Safety

Per constitutional requirement, all state must be terminal-scoped:
- Output directory: `.claude/state/terminals/{terminal_id}/adversarial-reviews/`
- Uses existing `state_paths.get_terminal_state_dir()` infrastructure
- Prevents concurrent terminal corruption

---

## Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|-----------|
| **Performance Efficiency** | Context reduced 97% (35KB → 1KB) | Additional subprocess overhead (~1-2s) |
| **Maintainability** | Predictable context growth | Additional runner code to maintain |
| **Reliability** | No context exhaustion during review | Requires subprocess error handling |
| **Operational Excellence** | On-demand detailed access (read files) | Lost conversational agent benefits |

---

## Multi-Terminal Safety

- **Safe**: Terminal-scoped state prevents cross-terminal contamination
- **Investigation Needed**: Verify subprocess isolation prevents race conditions
- **Implementation**: Uses existing `state_paths.py` infrastructure

---

## Implementation

### Phase 1: Infrastructure (MUST)
- Create agent scripts from existing agent specs
- Implement adversarial_runner.py with terminal-scoped state
- Add error handling and timeout management

### Phase 2: Integration (MUST)
- Update plan-workflow SKILL.md to use Bash pattern
- Add --mode flag support (full/light)
- Preserve adversarial-critic meta-analysis phase
- Add on-demand file reading

### Phase 3: Validation (MUST)
- Compare results: Agent tool vs subprocess runner
- Verify context reduction (measure token impact)
- Test multi-terminal isolation
- Validate error handling paths

---

## Consequences

### Positive
- Context reduction from ~30KB to ~1KB (97% reduction)
- No more context exhaustion during adversarial review
- Tunable review intensity (full/light modes)
- Persistent findings for later analysis

### Negative
- Additional ~300 lines of runner code to maintain
- Lost conversational debugging (can't see agent reasoning)
- ~1-2s subprocess overhead vs direct Agent tool
- Requires creating standalone agent scripts

### Mitigations
- Comprehensive error handling and logging
- Test coverage for all subprocess paths
- Fallback to Agent tool if subprocess approach fails

---

## Alternatives Considered

### Alternative A: Proactive compaction before review
**Rejected:** Requires manual intervention, doesn't scale
### Alternative B: Reduce agent count
**Rejected:** Loses comprehensive coverage
### Alternative C: Use Agent tool with run_in_background
**Rejected:** Agent tool doesn't support background execution that suppresses context delivery

---

## Evidence Sources

- Context exhaustion logs from plan-workflow review runs
- Agent tool documentation (Claude Code reference)
- state_paths.py infrastructure for multi-terminal isolation
- TurboAI blog post on Claude Code context management (analogical)
