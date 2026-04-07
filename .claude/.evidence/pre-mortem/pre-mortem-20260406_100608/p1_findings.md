## Triage Classification
failure/RCA — RCA package (packages/rca/) is a root-cause analysis tool with hooks, state management, and confidence tracking

## Dispatched Specialists
- adversarial-compliance
- adversarial-logic
- adversarial-performance
- adversarial-security
- adversarial-testing
- adversarial-quality
- adversarial-qa

## Specialist Findings Summary

### adversarial-compliance
- [HIGH] State Directory Path Inconsistency Between Modules (packages/rca/src/rca/action_tracer.py)
- [MEDIUM] Emoji Characters in TYPE_LABELS Break Rendering (packages/rca/src/rca/flow_visualizer.py)
- [HIGH] Evidence Tier Classification Mismatch for git_bisect_result (packages/rca/src/rca/evidence_tier.py)
- [MEDIUM] PHASE_ORDER Does Not Match SKILL.md Phase Names (packages/rca/src/rca/phase_state_manager.py)
- [MEDIUM] run_regression_check Days Parameter Is Non-Functional (packages/rca/src/rca/session.py)
- [MEDIUM] Hardcoded CKS Fallback Import Path (packages/rca/src/rca/evidence_tier.py)
- [MEDIUM] Hook Warning Uses stderr Violating CLAUDE.md Convention (packages/rca/skill/hooks/PostToolUse_rca_search_validator.py)
- [HIGH] FlowVisualizer Mermaid Styling References Wrong Node IDs (packages/rca/src/rca/flow_visualizer.py)
- [LOW] classify_action Has Hardcoded Tool Name Patterns (packages/rca/src/rca/action_tracer.py)
- [LOW] PhaseStateManager State Directory Not Validated (packages/rca/src/rca/phase_state_manager.py)

### adversarial-logic
- [BLOCKER] _determine_verdict() always returns REJECTED regardless of input. All three bran (temporal_check.py:387-393)
- [HIGH] FixRegistry.__init__ accepts only 'cache_dir' parameter, but _test() passes 'max (fix_registry.py:418)
- [MEDIUM] _calculate_confidence() assigns 0.3 confidence to hypotheses with no warnings bu (temporal_check.py:401-405)
- [LOW] similarity_to() is asymmetric: fp1.similarity_to(fp2) != fp2.similarity_to(fp1)  (stack_trace_fingerprint.py:54-89)
- [LOW] _calculate_confidence() has base_confidence=0.5 even when characteristics list i (cognitive_mode_selector.py:358-370)
- [LOW] time_to_verify calculation silently catches all exceptions without logging. If t (outcome_recorder.py:148-162)

### adversarial-performance
- [MEDIUM] TOCTOU race condition in FixRegistry._load_registry (packages/rca/src/rca/fix_registry.py)
- [MEDIUM] TOCTOU race condition in LibraryDocsCache._load_cache (packages/rca/src/rca/library_docs_cache.py)
- [MEDIUM] TOCTOU race condition in cli._get_session_id (packages/rca/src/rca/cli.py)
- [MEDIUM] TOCTOU race condition in ActionTracer._load_or_create_graph (packages/rca/src/rca/action_tracer.py)
- [MEDIUM] TOCTOU race condition in PhaseStateManager.restore (packages/rca/src/rca/phase_state_manager.py)
- [LOW] N+1 file read pattern in PhaseStateManager.list_phases (spool mode) (packages/rca/src/rca/phase_state_manager.py)
- [LOW] N+1 comparison pattern in FixRegistry.find_similar (packages/rca/src/rca/fix_registry.py)
- [LOW] Missing cache invalidation on write failure in LibraryDocsCache (packages/rca/src/rca/library_docs_cache.py)

### adversarial-qa
- [BLOCKER] Three test files exist with comprehensive test cases BUT the modules under test  (tests/test_hypothesis_generator.py, tests/test_error_signature.py, tests/test_stack_trace_fingerprint.py)
- [BLOCKER] Hardcoded version assertion will always fail. Test asserts 'rca.__version__ == " (tests/test_integration_e2e.py:15)
- [HIGH] Tests use weak assertion patterns that pass even when extraction fails. Example: (tests/test_stack_trace_fingerprint.py:582-595 (test_extract_from_typescript_error), :604-614 (test_extract_from_go_error), :668-684 (test_extract_normalizes_paths))
- [HIGH] Edge case tests use no-op assertion patterns like 'assert fp is not None or True (tests/test_stack_trace_fingerprint.py:806-874 (TestEdgeCases))
- [MEDIUM] Confidence clamping logic uses nested min/max that may not handle all edge cases (src/rca/hypothesis_generator.py:563 (calculate_hypothesis_confidence clamping))
- [MEDIUM] FixRegistry._test() calls constructor with invalid kwarg 'max_age_hours=24' but  (src/rca/fix_registry.py:418 (_test function))
- [MEDIUM] Test comment references a BUG in the code being tested: 'Use an issue that doesn (tests/test_simple_rca_engine.py:461-469 (test_execute_causal_loop_analysis comment))

### adversarial-quality
- [HIGH] Missing Mapping import causes NameError in hypothesis_generator.py (packages/rca/src/rca/hypothesis_generator.py)
- [MEDIUM] ConfidenceTracker.update() ignores evidence_supports parameter (packages/rca/src/rca/confidence_tracker.py)
- [MEDIUM] HypothesisScorer._ensure_evidence_tier() returns None on repeated calls (packages/rca/src/rca/hypothesis_scorer.py)
- [MEDIUM] Emoji characters in evidence_tier.py output cause cross-platform issues (packages/rca/src/rca/evidence_tier.py)
- [MEDIUM] Hardcoded Windows path in fix_registry.py and pattern_registry.py (packages/rca/src/rca/fix_registry.py)
- [LOW] Silent exception handling masks errors throughout codebase (packages/rca/src/rca/session.py)
- [LOW] HypothesisScorer.add_hypothesis uses inconsistent scoring formula (packages/rca/src/rca/hypothesis_scorer.py)
- [LOW] metrics_tracker.py uses PROJECT_ROOT computed path without verification (packages/rca/src/rca/metrics_tracker.py)

### adversarial-security
- [MEDIUM] subprocess.run with user-controlled input in temporal_check.py (P:/packages/rca/src/rca/temporal_check.py)
- [LOW] Plaintext JSON file storage without encryption in fix_registry.py and pattern_re (P:/packages/rca/src/rca/fix_registry.py)
- [MEDIUM] runpy.run_path executing hook files in hook_launcher.py (P:/packages/rca/src/rca/hook_launcher.py)
- [LOW] Session state written to plaintext JSON in session_preflight.py (P:/packages/rca/src/rca/session_preflight.py)
- [LOW] subprocess.run in converge_validator.py with module paths (P:/packages/rca/src/rca/converge_validator.py)
- [LOW] JSON parsing without schema validation in multiple files (P:/packages/rca/src/rca/pattern_registry.py)

### adversarial-testing
- [HIGH] Integration test does not test actual RCA workflow (P:/packages/rca/tests/test_integration_e2e.py)
- [HIGH] Vague assertions in simple_rca_engine tests allow wrong behavior to pass (P:/packages/rca/tests/test_simple_rca_engine.py)
- [MEDIUM] calculate_hypothesis_confidence function has no tests (P:/packages/rca/src/rca/hypothesis_generator.py)
- [MEDIUM] generate_hypotheses_from_evidence with empty evidence list not tested (P:/packages/rca/src/rca/hypothesis_generator.py)
- [MEDIUM] Fault localization parse_coverage_json not tested with real coverage data (P:/packages/rca/tests/test_fault_localization.py)
- [MEDIUM] test_identify_feedback_loops uses leading input that produces expected output (P:/packages/rca/tests/test_simple_rca_engine.py)
- [MEDIUM] SBFL formula implementations lack edge case validation (P:/packages/rca/src/rca/fault_localization.py)
- [LOW] Test for confidence_tracker handles NaN and infinity but allows them (P:/packages/rca/tests/test_confidence_tracker.py)
- [LOW] test_fishbone_generates_causes_for_machine_category has no meaningful assertion (P:/packages/rca/tests/test_simple_rca_engine.py)
- [LOW] test_hypothesis_generator missing custom weight edge case test (P:/packages/rca/tests/test_hypothesis_generator.py)
