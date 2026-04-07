# Work: skill-ship Policy Routing and Evaluator Separation

## What was built

### Phase 1.7 Policy Routing
- Added phase_1_7_policy_routing to SKILL.md workflow_steps (blocks phase_2)
- Added Phase 1.7 section to references/workflow-phases.md
- Created config/policy.json - artifact type routing matrix with 5 artifact types + default
- Each entry: {phases: [...], risk_level: low|medium|high}
- Unknown artifact types fall back to default (includes 3e/3f)

### Evaluator/Judge Separation
- Split Phase 3d into Phase 3e (Evaluator) and Phase 3f (Judge)
- Added phase_3e_evaluator and phase_3f_judge to SKILL.md workflow_steps
- Added Phase 3e/3f sections to references/workflow-phases.md
- Created references/evaluator-judge-prompts.md with verbatim prompt templates
- Evaluator: 7 rubric lenses, structured JSON findings, evidence requirement
- Judge: policy-driven decision (critical->fail, dimension thresholds, risk_level overrides)

### Test Files
- tests/test_policy_routing.py - 10 tests
- tests/test_evaluator.py - 10 tests
- tests/test_judge.py - 15 tests
- All 35 tests pass

### Bug Fixes (auto_verify.py)
- STATE-001 false positive: restructured is_stateful_plan()
- RTM-003 false positive: fixed has_acceptance_header regex

## Files Modified/Created
- skill-ship/config/policy.json (NEW)
- skill-ship/references/evaluator-judge-prompts.md (NEW)
- skill-ship/tests/test_policy_routing.py (NEW)
- skill-ship/tests/test_evaluator.py (NEW)
- skill-ship/tests/test_judge.py (NEW)
- skill-ship/SKILL.md (updated)
- skill-ship/references/workflow-phases.md (updated)
- packages/sdlc/skills/planning/__lib/auto_verify.py (2 bug fixes)
- skill-ship-policy-routing-and-evaluator-separation.md plan (marked completed)

## Policy Routing Table
prompt_skill: 3a,3b low
new_skill: 3a,3b,3c,3e,3f medium
orchestrator: 3a,3b,3c,3d,3e,3f high
contract_change: 3a,3b,3c,3d,3e,3f high
distribution_update: 3a,3b,3c medium
default: 3a,3b,3c,3e,3f medium

## Judge Decision Policy
1. Any critical -> fail
2. problem_fit<3 OR adaptability<3 OR failure_tolerance<3 -> fail
3. high risk + no critical -> conditional_pass
4. Otherwise -> pass