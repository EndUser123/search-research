# Review Target

Target: P:/packages/snapshot

## Package Overview
snapshot is a Claude Code plugin providing session snapshot capture and restore.
V2 handoff envelope with resume snapshot, decision register, evidence index, and checksum validation.

## Source Structure
-  - Hook entry points (authoritative)
-  - Core library modules
-  - Alternative hook locations
-  - Test suite
-  - Skill definitions

## Python Files (99):
- P:\packages\snapshot\assets\banners\generate_banner.py
- P:\packages\snapshot\core\__init__.py
- P:\packages\snapshot\core\hooks\__init__.py
- P:\packages\snapshot\core\hooks\__lib\__init__.py
- P:\packages\snapshot\examples\basic_usage.py
- P:\packages\snapshot\scripts\__init__.py
- P:\packages\snapshot\scripts\checkpoint_chain.py
- P:\packages\snapshot\scripts\checkpoint_ops.py
- P:\packages\snapshot\scripts\cli.py
- P:\packages\snapshot\scripts\config.py
- P:\packages\snapshot\scripts\fix_test_imports.py
- P:\packages\snapshot\scripts\hooks\__init__.py
- P:\packages\snapshot\scripts\hooks\__lib\__init__.py
- P:\packages\snapshot\scripts\hooks\__lib\architecture_capture.py
- P:\packages\snapshot\scripts\hooks\__lib\capture_cache.py
- P:\packages\snapshot\scripts\hooks\__lib\dependency_state.py
- P:\packages\snapshot\scripts\hooks\__lib\dynamic_sections.py
- P:\packages\snapshot\scripts\hooks\__lib\error_capture.py
- P:\packages\snapshot\scripts\hooks\__lib\git_state.py
- P:\packages\snapshot\scripts\hooks\__lib\haiku_prompt.py
- P:\packages\snapshot\scripts\hooks\__lib\handover.py
- P:\packages\snapshot\scripts\hooks\__lib\hook_input_validation.py
- P:\packages\snapshot\scripts\hooks\__lib\hook_schema.py
- P:\packages\snapshot\scripts\hooks\__lib\parallel_capture.py
- P:\packages\snapshot\scripts\hooks\__lib\project_root.py
- P:\packages\snapshot\scripts\hooks\__lib\session_registry.py
- P:\packages\snapshot\scripts\hooks\__lib\snapshot_accumulator.py
- P:\packages\snapshot\scripts\hooks\__lib\snapshot_files.py
- P:\packages\snapshot\scripts\hooks\__lib\snapshot_store.py
- P:\packages\snapshot\scripts\hooks\__lib\snapshot_v2.py
- P:\packages\snapshot\scripts\hooks\__lib\task_identity_manager.py
- P:\packages\snapshot\scripts\hooks\__lib\terminal_detection.py
- P:\packages\snapshot\scripts\hooks\__lib\terminal_file_registry.py
- P:\packages\snapshot\scripts\hooks\__lib\test_state.py
- P:\packages\snapshot\scripts\hooks\__lib\transcript.py
- P:\packages\snapshot\scripts\hooks\__lib\user_intent.py
- P:\packages\snapshot\scripts\hooks\__lib\validation_utils.py
- P:\packages\snapshot\scripts\hooks\PreCompact.py
- P:\packages\snapshot\scripts\hooks\PreCompact_commitment_tracker.py
- P:\packages\snapshot\scripts\hooks\precompact_imports_patch.py
- P:\packages\snapshot\scripts\hooks\PreCompact_snapshot_capture.py
- P:\packages\snapshot\scripts\hooks\PreCompact_workflow_checkpoint.py
- P:\packages\snapshot\scripts\hooks\SessionEnd_tldr.py
- P:\packages\snapshot\scripts\hooks\SessionStart_snapshot_restore.py
- P:\packages\snapshot\scripts\hooks\SessionStart_tldr.py
- P:\packages\snapshot\scripts\hooks\userpromptsubmit_task_injector.py
- P:\packages\snapshot\scripts\migrate.py
- P:\packages\snapshot\scripts\models.py
- P:\packages\snapshot\scripts\protocol.py
- P:\packages\snapshot\scripts\tests\__init__.py
- P:\packages\snapshot\scripts\tests\conftest.py
- P:\packages\snapshot\scripts\tests\test_handoff_hooks.py
- P:\packages\snapshot\scripts\tests\test_hook_schema_validation.py
- P:\packages\snapshot\scripts\tests\test_ups_task_injector.py
- P:\packages\snapshot\skills\track\track.py
- P:\packages\snapshot\sub_agent_invocation_example.py
- P:\packages\snapshot\tests\add_non_english_tests.py
- P:\packages\snapshot\tests\conftest.py
- P:\packages\snapshot\tests\test_canonical_goal_extraction.py
- P:\packages\snapshot\tests\test_conflict_detection.py
- P:\packages\snapshot\tests\test_context_gathering_boundaries.py
- P:\packages\snapshot\tests\test_continuation_rule.py
- P:\packages\snapshot\tests\test_correction_message_detection.py
- P:\packages\snapshot\tests\test_dependency_state.py
- P:\packages\snapshot\tests\test_deterministic_checksums.py
- P:\packages\snapshot\tests\test_edge_case_transcripts.py
- P:\packages\snapshot\tests\test_envelope_schema_validation.py
- P:\packages\snapshot\tests\test_git_state.py
- P:\packages\snapshot\tests\test_haiku_conversation_summary.py
- P:\packages\snapshot\tests\test_handoff_context_preservation.py
- P:\packages\snapshot\tests\test_handoff_full_integration.py
- P:\packages\snapshot\tests\test_handoff_integration.py
- P:\packages\snapshot\tests\test_handoff_meta_discussion.py
- P:\packages\snapshot\tests\test_handoff_regression_skill_capture.py
- P:\packages\snapshot\tests\test_handoff_skill_definition_filter.py
- P:\packages\snapshot\tests\test_handoff_task_injector.py
- P:\packages\snapshot\tests\test_handoff_ttl.py
- P:\packages\snapshot\tests\test_intent_classification.py
- P:\packages\snapshot\tests\test_intent_integration.py
- P:\packages\snapshot\tests\test_last_substantive_message_integration.py
- ... and 19 more
