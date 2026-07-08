# Abstraction Audit Manifest

- repo_root: `P:\packages\.claude-marketplace`
- created_at: `2026-07-08T01:24:23.085074+00:00`
- coverage_authority: `whole_repo_static`

## Counts

- skills: 167
- commands: 172
- references: 270
- hooks: 337
- tests: 1164
- evals: 81
- registries: 63
- other: 24440

## Missing Terms

- none

## Risk Flags

### possible_false_full_coverage_claim
- plugins/search-research/tests/unit/test_smart_chunker.py
- plugins/cc-skills-sdlc/skills/planning/references/adversarial-agent-prompts.md
- plugins/cc-skills-analysis/skills/debrief/references/report-contracts.md

### runtime_advisory_confusion
- plugins/cc-skills-architect/skills/ask/lib/abstraction_audit_manifest.py
- plugins/cc-skills-architect/skills/ask/tests/test_abstraction_audit_manifest.py

### permission_deferral_language
- plugins/cc-skills-thinking/skills/s/api_responses_log.jsonl
- plugins/cc-skills-sdlc/skills/design/validate_templates.py
- plugins/cc-skills-sdlc/skills/go/SKILL.md
- plugins/cc-skills-sdlc/skills/wiki/SKILL.md
- plugins/cc-skills-media/skills/nlm/references/workflows.md
- plugins/cc-skills-lab/skills/concept-mapper/SKILL.md
- plugins/cc-skills-architect/skills/ask/SKILL.md
- plugins/cc-skills-architect/skills/ask/lib/abstraction_audit_manifest.py
- plugins/cc-skills-architect/skills/ask/tests/test_abstraction_audit_manifest.py
- plugins/cc-skills-analysis/skills/debrief/tests/test_report_contracts.py
- plugins/cc-aca-epistemic/__lib/anti_sycophancy/lazy_closure_detector.py
- plugins/cc-aca-authority/__lib/response_intent.py
- plugins/cc-aca-authority/hooks/stop/stop_permission_stall.py

### wiki_ingest_or_auto_write
- shared/README.md
- shared/docs/wiki_cks_ingest_queue.md
- plugins/cc-skills-architect/skills/ask/lib/abstraction_audit_manifest.py
- plugins/cc-skills-architect/skills/ask/tests/test_abstraction_audit_manifest.py
- plugins/cc-skills-analysis/skills/debrief/references/completion-evidence-contract.md
- plugins/cc-skills-analysis/skills/debrief/references/thought-partner-addendum.md
- plugins/cc-skills-analysis/skills/debrief/tests/test_completion_evidence_contract.py
- plugins/cc-skills-analysis/skills/debrief/tests/test_no_new_triggers_structural.py
- plugins/cc-skills-analysis/skills/debrief/tests/test_report_contracts.py
- plugins/cc-skills-analysis/skills/debrief/tests/test_thought_partner_addendum.py

### telemetry_swallowing
- plugins/snapshot/skills/id/SKILL.md
- plugins/cc-skills-utils/skills/main/references/narrative-intent-detector.md
- plugins/cc-skills-sdlc/skills/__lib/adversarial_review_protocol.md
- plugins/cc-skills-architect/skills/ask/lib/abstraction_audit_manifest.py
- plugins/cc-skills-architect/skills/ask/tests/test_abstraction_audit_manifest.py
- plugins/cc-aca-authority/hooks/stop/Stop_behavior_gates.py

### missing_feedback_loop_terms
- none

## Recommended Read Set (top 30)

- plugins/cc-skills-architect/skills/ask/lib/abstraction_audit_manifest.py
- plugins/cc-skills-architect/skills/ask/tests/test_abstraction_audit_manifest.py
- plugins/cc-skills-analysis/skills/debrief/references/report-contracts.md
- plugins/cc-skills-analysis/skills/debrief/tests/test_report_contracts.py
- plugins/improve-partner/skills/improve/SKILL.md
- plugins/cc-skills-architect/skills/ask/SKILL.md
- plugins/red-team/commands/red-team.md
- plugins/cc-skills-analysis/skills/debrief/SKILL.md
- plugins/cc-skills-analysis/skills/claude-audit/SKILL.md
- plugins/cc-skills-analysis/skills/skill-audit/SKILL.md
- plugins/cc-skills-analysis/skills/debrief/references/completion-evidence-contract.md
- plugins/cc-aca-observability/__lib/data/reflexion_verifications.jsonl
- plugins/cc-skills-sdlc/skills/review/SKILL.md
- plugins/cc-skills-analysis/skills/debrief/references/thought-partner-addendum.md
- plugins/cc-skills-analysis/skills/debrief/tests/test_cross_skill_transfer.py
- plugins/cc-skills-analysis/skills/debrief/tests/test_completion_evidence_contract.py
- plugins/cc-skills-analysis/skills/debrief/tests/test_no_new_triggers_structural.py
- plugins/cc-skills-sdlc/skills/go/SKILL.md
- plugins/search-research/.aid/search-research_sig.md
- plugins/search-research/.aid/search-research/search-research_full.md
- plugins/cc-skills-thinking/skills/s/api_responses_log.jsonl
- plugins/cc-skills-analysis/skills/debrief/references/bad-behavior-rubric.md
- plugins/cc-skills-sdlc/skills/wiki/SKILL.md
- plugins/cc-skills-analysis/skills/debrief/tests/test_thought_partner_addendum.py
- plugins/cc-skills-analysis/skills/debrief/references/cross-skill-transfer-check.md
- plugins/cc-skills-analysis/skills/debrief/tests/test_routing_by_affordances.py
- plugins/cc-skills-utils/skills/git/references/batch/batch-evidence-format.md
- plugins/cc-skills-sdlc/skills/pre-mortem/references/pre-mortem-evidence-tiers.md
- plugins/cc-skills-sdlc/skills/go/scripts/orchestrate.py
- plugins/cc-skills-sdlc/skills/refactor/scan_targets.txt

## Proof Limits

This manifest is whole-repo static evidence only. It does not prove
runtime activation, hook calibration, behavior change, or LLM compliance.

To claim runtime activation, run the Plugin Mutation Checklist (6 steps)
and drive the user path end-to-end before claiming anything is 'live'.