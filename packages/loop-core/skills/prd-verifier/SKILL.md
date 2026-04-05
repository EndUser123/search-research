# PRD Verifier Skill

**Status**: Stub (contract defined, implementation pending)

## Purpose

Verifies implementation completeness and quality against PRD requirements, specifications, and quality standards. This skill is invoked by the loop-core platform before loop exit when `require_verification_pass` is enabled.

## Input/Output Contract

### Inputs

The verification skill receives the following context from loop-core:

1. **PRD/Spec Path** (required)
   - Source: Config or plan metadata
   - Format: File path (relative to project root)
   - Example: `docs/PRD.md` or `spec/requirements.md`
   - Purpose: Defines requirements to verify against

2. **Plan Path** (required)
   - Source: Loop state (from `loop_state.json`)
   - Format: File path (relative to project root)
   - Example: `.claude/loop/plan-{terminal_id}.md`
   - Purpose: Defines planned implementation to verify

3. **Codebase Directory** (required)
   - Source: Current working directory
   - Format: Directory path
   - Example: `/path/to/project`
   - Purpose: Source code to verify

4. **Verification Fields** (optional, defaults from config)
   - Source: `config.yaml` verification.fields
   - Format: List of field names
   - Default: `["prd_coverage", "spec_compliance", "implementation_quality"]`
   - Purpose: Define which verification aspects to include

### Outputs

The verification skill produces the following artifacts:

1. **Verification Report** (required)
   - Path: From `config.yaml` verification.write_report
   - Default: `.claude/loop/verification-report.md`
   - Format: Markdown
   - Required sections:
     ```markdown
     # Verification Report

     ## Summary
     [PASS/FAIL] - Brief overall status

     ## PRD Coverage
     - Requirements addressed: X/Y
     - Missing requirements: [list]
     - Coverage percentage: Z%

     ## Spec Compliance
     - Spec requirements met: X/Y
     - Deviations: [list]
     - Compliance percentage: Z%

     ## Implementation Quality
     - Code quality score: X/Y
     - Critical issues: [list]
     - Recommendations: [list]

     ## Detailed Findings
     [Per-field detailed analysis]
     ```

2. **Verification Passed Flag** (required)
   - Location: `loop_state.json`
   - Key: `verification_passed`
   - Type: Boolean
   - Purpose: Signals to loop-core whether verification passed
   - Format:
     ```json
     {
       "verification_passed": true|false,
       "verification_report": ".claude/loop/verification-report.md",
       "verification_timestamp": "2026-03-15T12:34:56Z"
     }
     ```

## Verification Fields

### prd_coverage
Verifies that all PRD requirements are addressed:
- Functional requirements implementation
- Non-functional requirements (performance, security, etc.)
- User stories and use cases
- Acceptance criteria

### spec_compliance
Verifies compliance with technical specifications:
- API contract adherence
- Data structure compliance
- Architecture pattern compliance
- Integration point correctness

### implementation_quality
Verifies code quality and best practices:
- Code organization and structure
- Error handling completeness
- Testing coverage
- Documentation quality
- Performance characteristics

## Invocation Context

This skill is automatically invoked by loop-core when:
1. Loop exit policy conditions are met
2. `require_verification_pass` is enabled in config
3. All other exit criteria are satisfied

## Error Handling

If verification fails:
- Set `verification_passed: false` in loop_state
- Write detailed findings to verification report
- Loop-core will NOT exit, allowing iteration to continue

If verification encounters an error:
- Report error to verification report
- Set `verification_passed: false`
- Log error to verifier.log

## Implementation Notes

**STUB STATUS**: This skill currently documents the contract. Implementation is pending TASK-015.

Future implementation should:
1. Parse PRD/spec for requirements
2. Analyze codebase for compliance
3. Generate structured markdown report
4. Update loop_state with verification result
5. Handle missing PRD/spec gracefully

## Configuration Integration

This skill integrates with `.claude/loop/config.yaml`:

```yaml
verification:
  enabled: true
  skill: prd-verifier  # This skill
  write_report: .claude/loop/verification-report.md
  fields:
    - prd_coverage
    - spec_compliance
    - implementation_quality
```

## Testing

Test cases should verify:
- PASS scenario: All requirements met
- FAIL scenario: Missing requirements
- FAIL scenario: Quality issues below threshold
- ERROR scenario: Missing PRD file
- ERROR scenario: Invalid codebase path
- PARTIAL scenario: Some requirements met

## Related Files

- Config schema: `scripts/config_schema.py` (VerificationConfig)
- Loop state: `scripts/state_manager.py`
- Exit policy: `scripts/loop_policy.py`
- Integration test: `tests/test_integration.py`
