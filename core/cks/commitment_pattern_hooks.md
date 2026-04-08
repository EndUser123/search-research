# Commitment Pattern Hooks for Error Attribution

**Source:** ADR-009
**Tags:** hooks,error-attribution,commitment-pattern,adr,behavioral-pattern
**Created:** 2025-12-29

## Summary

Two-layer commitment pattern to prevent Claude Code from blaming external factors (git, cache, services) for errors that were actually caused by its own recent code changes.

## Implementation

### Layer 1: PostToolUse Injection (error_attribution_validator.py v2.1.0)
- Detects tool errors
- Injects commitment checkpoint requiring explicit YES/NO with evidence
- Sets commitment_required flag in session state

### Layer 2: Stop Hook Validation (constitutional_enforcer.py v2.2.0)
- Validates commitment was fulfilled before allowing external blame
- Blocks response patterns like "git checkout caused this" without self-check
- Uses CommitmentValidator class with pass/block pattern lists

## Research Basis

- Scott Spence forced eval pattern
- 84%% vs 20%% effectiveness with explicit commitment
- Block-at-submit pattern (enterprise best practice)

## Files

- .claude/hooks/error_attribution_validator.py
- .claude/hooks/constitutional_enforcer.py
- .claude/hooks/tool_sequence_tracker.py
- __csf.nip/docs/adr/ADR-009-COMMITMENT_PATTERN_HOOKS_2025-12.md
