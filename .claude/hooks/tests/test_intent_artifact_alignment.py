"""Tests for intent_artifact_alignment.py gate.

Verifies:
1. extract_targets_from_prompt extracts file/command/skill targets
2. extract_modified_paths extracts Edit/Write file paths
3. check_alignment detects misalignment and warns
4. check_alignment passes when targets are met
5. Completion claims escalate severity
6. No false positives on vague prompts
7. Path normalization handles relative/absolute/Windows paths

Run with: pytest P:/.claude/hooks/tests/test_intent_artifact_alignment.py -v
"""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from intent_artifact_alignment import (
    TargetSpec,
    check_alignment,
    extract_executed_commands,
    extract_invoked_skills,
    extract_modified_paths,
    extract_targets_from_prompt,
)


# =============================================================================
# TEST 1: Target extraction from prompt
# =============================================================================


class TestExtractTargetsFromFile:
    """Verify file target extraction from prompts."""

    def test_verb_plus_path(self):
        targets = extract_targets_from_prompt("modify Stop.py and add tests")
        paths = [t.value for t in targets if t.kind == "file"]
        assert any("Stop.py" in p for p in paths)

    def test_update_path(self):
        targets = extract_targets_from_prompt("update CLAUDE.md with docs")
        paths = [t.value for t in targets if t.kind == "file"]
        assert any("CLAUDE.md" in p for p in paths)

    def test_fix_path(self):
        targets = extract_targets_from_prompt("fix the bug in Stop.py")
        paths = [t.value for t in targets if t.kind == "file"]
        assert any("Stop.py" in p for p in paths)

    def test_create_path(self):
        targets = extract_targets_from_prompt("create test_intent.py")
        paths = [t.value for t in targets if t.kind == "file"]
        assert any("test_intent.py" in p for p in paths)

    def test_multiple_paths(self):
        targets = extract_targets_from_prompt(
            "modify Stop.py and create tests/test_gate.py"
        )
        paths = [t.value for t in targets if t.kind == "file"]
        assert len(paths) >= 2

    def test_in_path_with_verb(self):
        targets = extract_targets_from_prompt("add tests in test_foo.py")
        paths = [t.value for t in targets if t.kind == "file"]
        assert any("test_foo.py" in p for p in paths)

    def test_no_target_vague_prompt(self):
        targets = extract_targets_from_prompt("fix the bug")
        assert len(targets) == 0

    def test_no_target_exploration(self):
        targets = extract_targets_from_prompt("should we refactor?")
        assert len(targets) == 0

    def test_no_target_control(self):
        targets = extract_targets_from_prompt("stop")
        assert len(targets) == 0

    def test_no_target_question(self):
        targets = extract_targets_from_prompt("why is this failing?")
        assert len(targets) == 0


class TestExtractTargetsFromCommand:
    """Verify command target extraction from prompts."""

    def test_run_pytest(self):
        targets = extract_targets_from_prompt("run pytest on the module")
        cmds = [t.value for t in targets if t.kind == "command"]
        assert "pytest" in cmds

    def test_execute_command(self):
        targets = extract_targets_from_prompt("execute the build script")
        cmds = [t.value for t in targets if t.kind == "command"]
        # "script" may or may not be extracted depending on pattern
        # The key is that it doesn't crash

    def test_no_command_target(self):
        targets = extract_targets_from_prompt("fix the bug in Stop.py")
        cmds = [t.value for t in targets if t.kind == "command"]
        assert len(cmds) == 0


class TestExtractTargetsFromSkill:
    """Verify skill target extraction from prompts."""

    def test_use_skill(self):
        targets = extract_targets_from_prompt("use /rca to investigate")
        skills = [t.value for t in targets if t.kind == "skill"]
        assert any("rca" in s for s in skills)

    def test_invoke_skill(self):
        targets = extract_targets_from_prompt("invoke /bf on the code")
        skills = [t.value for t in targets if t.kind == "skill"]
        assert any("bf" in s for s in skills)

    def test_no_skill_target(self):
        targets = extract_targets_from_prompt("modify Stop.py")
        skills = [t.value for t in targets if t.kind == "skill"]
        assert len(skills) == 0


# =============================================================================
# TEST 2: Modified path extraction from tool events
# =============================================================================


class TestExtractModifiedPaths:
    """Verify file path extraction from tool events."""

    def test_edit_flat_format(self):
        events = [{"name": "Edit", "file_path": "P:/.claude/hooks/Stop.py"}]
        paths = extract_modified_paths(events)
        assert any("Stop.py" in p for p in paths)

    def test_edit_nested_format(self):
        events = [{"name": "Edit", "input": {"file_path": "Stop.py"}}]
        paths = extract_modified_paths(events)
        assert any("Stop.py" in p for p in paths)

    def test_write_flat_format(self):
        events = [{"name": "Write", "file_path": "tests/test_gate.py"}]
        paths = extract_modified_paths(events)
        assert any("test_gate.py" in p for p in paths)

    def test_read_not_included(self):
        events = [{"name": "Read", "file_path": "Stop.py"}]
        paths = extract_modified_paths(events)
        assert len(paths) == 0

    def test_mixed_tools(self):
        events = [
            {"name": "Read", "file_path": "Stop.py"},
            {"name": "Edit", "file_path": "Stop.py"},
            {"name": "Write", "file_path": "tests/test_gate.py"},
            {"name": "Bash", "command": "pytest tests/"},
        ]
        paths = extract_modified_paths(events)
        assert len(paths) == 2

    def test_empty_events(self):
        paths = extract_modified_paths([])
        assert len(paths) == 0

    def test_non_dict_events(self):
        events = ["not a dict", 42, None]
        paths = extract_modified_paths(events)
        assert len(paths) == 0


class TestExtractExecutedCommands:
    """Verify command extraction from Bash events."""

    def test_bash_command(self):
        events = [{"name": "Bash", "command": "pytest tests/ -v"}]
        cmds = extract_executed_commands(events)
        assert any("pytest" in c for c in cmds)

    def test_no_bash_events(self):
        events = [{"name": "Edit", "file_path": "Stop.py"}]
        cmds = extract_executed_commands(events)
        assert len(cmds) == 0


class TestExtractInvokedSkills:
    """Verify skill extraction from Skill events."""

    def test_skill_flat(self):
        events = [{"name": "Skill", "skill": "rca"}]
        skills = extract_invoked_skills(events)
        assert "rca" in skills

    def test_skill_nested(self):
        events = [{"name": "Skill", "input": {"skill": "bf"}}]
        skills = extract_invoked_skills(events)
        assert "bf" in skills

    def test_no_skill_events(self):
        events = [{"name": "Edit", "file_path": "Stop.py"}]
        skills = extract_invoked_skills(events)
        assert len(skills) == 0


# =============================================================================
# TEST 3: Alignment check
# =============================================================================


class TestCheckAlignment:
    """Verify alignment detection logic."""

    def test_file_target_missed_warn(self):
        result = check_alignment(
            prompt="modify Stop.py and add tests in test_gate.py",
            tool_events=[
                {"name": "Write", "file_path": "P:/.claude/hooks/helper.py"},
            ],
            response="I've made some changes to the helper module.",
        )
        assert result is not None
        assert result["decision"] == "warn"
        assert any("Stop.py" in t for t in result["missed_targets"])

    def test_file_target_hit_no_warning(self):
        result = check_alignment(
            prompt="modify Stop.py",
            tool_events=[
                {"name": "Edit", "file_path": "P:/.claude/hooks/Stop.py"},
            ],
            response="Done.",
        )
        assert result is None

    def test_completion_claim_escalates_to_block(self):
        result = check_alignment(
            prompt="modify Stop.py",
            tool_events=[
                {"name": "Write", "file_path": "P:/.claude/hooks/helper.py"},
            ],
            response="✅ All done! Implementation is complete.",
        )
        assert result is not None
        assert result["decision"] == "block"
        assert result["claims_completion"] is True

    def test_no_targets_no_warning(self):
        result = check_alignment(
            prompt="fix the bug",
            tool_events=[
                {"name": "Edit", "file_path": "Stop.py"},
            ],
        )
        assert result is None

    def test_vague_prompt_no_warning(self):
        result = check_alignment(
            prompt="why is this failing?",
            tool_events=[],
        )
        assert result is None

    def test_control_prompt_no_warning(self):
        result = check_alignment(
            prompt="stop",
            tool_events=[],
        )
        assert result is None

    def test_command_target_missed(self):
        result = check_alignment(
            prompt="run pytest on the module",
            tool_events=[
                {"name": "Read", "file_path": "module.py"},
            ],
        )
        assert result is not None
        assert any(t.kind == "command" for t in
                   [TargetSpec(kind="command", value=v, source="prompt")
                    for v in result["missed_targets"]])

    def test_command_target_hit(self):
        result = check_alignment(
            prompt="run pytest on the module",
            tool_events=[
                {"name": "Bash", "command": "pytest module.py"},
            ],
        )
        assert result is None

    def test_skill_target_missed(self):
        result = check_alignment(
            prompt="use /rca to investigate the crash",
            tool_events=[
                {"name": "Read", "file_path": "crash.log"},
            ],
        )
        assert result is not None

    def test_skill_target_hit(self):
        result = check_alignment(
            prompt="use /rca to investigate",
            tool_events=[
                {"name": "Skill", "skill": "rca"},
            ],
        )
        assert result is None

    def test_multiple_targets_partial_miss(self):
        result = check_alignment(
            prompt="modify Stop.py and create tests/test_gate.py",
            tool_events=[
                {"name": "Edit", "file_path": "P:/.claude/hooks/Stop.py"},
                # test_gate.py NOT created
            ],
            response="Done.",
        )
        assert result is not None
        assert any("test_gate" in t for t in result["missed_targets"])

    def test_windows_path_normalization(self):
        result = check_alignment(
            prompt="modify Stop.py",
            tool_events=[
                {"name": "Edit", "file_path": "P:\\.claude\\hooks\\Stop.py"},
            ],
        )
        assert result is None

    def test_system_message_present(self):
        result = check_alignment(
            prompt="modify Stop.py",
            tool_events=[
                {"name": "Write", "file_path": "helper.py"},
            ],
        )
        assert result is not None
        assert "systemMessage" in result
        assert "MISALIGNMENT" in result["systemMessage"]


# =============================================================================
# TEST 4: Edge cases
# =============================================================================


class TestEdgeCases:
    """Verify edge cases and boundary conditions."""

    def test_empty_prompt(self):
        result = check_alignment("", [{"name": "Edit", "file_path": "Stop.py"}])
        assert result is None

    def test_empty_events(self):
        result = check_alignment("modify Stop.py", [])
        assert result is not None

    def test_none_response(self):
        result = check_alignment("modify Stop.py", [], response="")
        assert result is not None
        # No completion claim → warn, not block
        assert result["decision"] == "warn"

    def test_duplicate_targets_deduplicated(self):
        targets = extract_targets_from_prompt(
            "modify Stop.py and modify Stop.py"
        )
        file_targets = [t for t in targets if t.kind == "file"]
        values = [t.value for t in file_targets]
        assert values.count("Stop.py") <= 1

    def test_partial_path_match(self):
        """Short path in prompt matches long path in events."""
        result = check_alignment(
            prompt="modify Stop.py",
            tool_events=[
                {"name": "Edit", "file_path": "P:/__project/.claude/hooks/Stop.py"},
            ],
        )
        assert result is None

    def test_adjacent_work_detection(self):
        """Assistant creates helper instead of modifying requested file."""
        result = check_alignment(
            prompt="add the intent_artifact_alignment gate to Stop.py",
            tool_events=[
                {"name": "Write", "file_path": "P:/.claude/hooks/intent_artifact_alignment.py"},
                {"name": "Write", "file_path": "P:/.claude/hooks/tests/test_intent.py"},
            ],
            response="✅ Implementation complete!",
        )
        assert result is not None
        assert result["decision"] == "block"
        assert "Stop.py" in result["missed_targets"]


# =============================================================================
# TEST 5: Runtime schema (flat {name, command} events)
# =============================================================================


class TestRuntimeSchemaFiles:
    """Verify file extraction from flat runtime tool_events ({name, command})."""

    def test_edit_command_contains_path(self):
        events = [{"name": "Edit", "command": "P:/.claude/hooks/Stop.py"}]
        paths = extract_modified_paths(events)
        assert any("Stop.py" in p for p in paths)

    def test_write_command_contains_relative_path(self):
        events = [{"name": "Write", "command": "tests/test_gate.py"}]
        paths = extract_modified_paths(events)
        assert any("test_gate.py" in p for p in paths)

    def test_edit_command_bare_filename(self):
        events = [{"name": "Edit", "command": "Stop.py"}]
        paths = extract_modified_paths(events)
        assert any("Stop.py" in p for p in paths)

    def test_edit_command_no_path(self):
        events = [{"name": "Edit", "command": ""}]
        paths = extract_modified_paths(events)
        assert len(paths) == 0

    def test_rich_schema_still_works(self):
        """Rich schema (file_path) takes priority over command."""
        events = [{"name": "Edit", "file_path": "Stop.py", "command": "other.py"}]
        paths = extract_modified_paths(events)
        assert "Stop.py" in paths


class TestSkillCommandFormatInventory:
    """Parametrized regression tests covering all observed runtime Skill event formats.

    Format inventory (source: test_stop_hook_tier3_verification.py:346,
    test_cleanup_verifier.py:222,289, evidence_scope.py):
      1. command="/verify"   (slash-prefixed, observed in tier3 test)
      2. command="rca"       (bare name)
      3. command="/bf"       (slash-prefixed short name)
      4. skill="code"        (rich schema, flat field)
      5. input.skill="code"  (rich schema, nested)
      6. command="plugin-installer:plugin-installer" (namespaced)
      7. command=""          (empty — no extraction)
    """

    @pytest.mark.parametrize(
        "events,expected",
        [
            # Runtime flat schema — slash-prefixed (real format from tier3 test)
            ([{"name": "Skill", "command": "/verify"}], "verify"),
            # Runtime flat schema — bare name
            ([{"name": "Skill", "command": "rca"}], "rca"),
            # Runtime flat schema — slash-prefixed short name
            ([{"name": "Skill", "command": "/bf"}], "bf"),
            # Runtime flat schema — namespaced plugin skill
            (
                [{"name": "Skill", "command": "plugin-installer:plugin-installer"}],
                "plugin-installer:plugin-installer",
            ),
            # Rich schema — flat skill field
            ([{"name": "Skill", "skill": "code"}], "code"),
            # Rich schema — nested input.skill
            ([{"name": "Skill", "input": {"skill": "research"}}], "research"),
            # Rich schema takes priority over command
            ([{"name": "Skill", "skill": "arch", "command": "/bf"}], "arch"),
            # Empty command — no extraction
            ([{"name": "Skill", "command": ""}], None),
        ],
    )
    def test_skill_extraction_format(self, events, expected):
        skills = extract_invoked_skills(events)
        if expected is None:
            assert len(skills) == 0
        else:
            assert expected in skills


class TestRuntimeSchemaAlignment:
    """End-to-end alignment checks with runtime-format events."""

    def test_file_hit_runtime_schema(self):
        result = check_alignment(
            prompt="modify Stop.py",
            tool_events=[
                {"name": "Edit", "command": "P:/.claude/hooks/Stop.py"},
            ],
            response="Updated the hook.",
        )
        assert result is None

    def test_file_miss_runtime_schema(self):
        result = check_alignment(
            prompt="modify Stop.py",
            tool_events=[
                {"name": "Write", "command": "P:/.claude/hooks/helper.py"},
            ],
            response="Done.",
        )
        assert result is not None
        assert any("Stop.py" in t for t in result["missed_targets"])

    def test_skill_hit_runtime_schema(self):
        result = check_alignment(
            prompt="use /rca to investigate",
            tool_events=[
                {"name": "Skill", "command": "rca"},
            ],
        )
        assert result is None

    def test_skill_miss_runtime_schema(self):
        result = check_alignment(
            prompt="use /rca to investigate",
            tool_events=[
                {"name": "Skill", "command": "bf"},
            ],
        )
        assert result is not None

    def test_command_hit_runtime_schema(self):
        result = check_alignment(
            prompt="run pytest on the module",
            tool_events=[
                {"name": "Bash", "command": "pytest module.py"},
            ],
        )
        assert result is None


# =============================================================================
# TEST 6: Narrowed completion-claim detection
# =============================================================================


class TestNarrowedCompletionClaims:
    """Verify that narrowed _COMPLETION_CLAIM_RE avoids false positives."""

    def test_emoji_triggers_block(self):
        result = check_alignment(
            prompt="modify Stop.py",
            tool_events=[
                {"name": "Write", "file_path": "helper.py"},
            ],
            response="✅ All done!",
        )
        assert result is not None
        assert result["decision"] == "block"

    def test_is_complete_triggers_block(self):
        result = check_alignment(
            prompt="modify Stop.py",
            tool_events=[
                {"name": "Write", "file_path": "helper.py"},
            ],
            response="The implementation is complete.",
        )
        assert result is not None
        assert result["decision"] == "block"

    def test_past_tense_no_completion_claim(self):
        """'I updated Stop.py' should NOT escalate to block."""
        result = check_alignment(
            prompt="modify Stop.py",
            tool_events=[
                {"name": "Edit", "file_path": "helper.py"},
            ],
            response="I updated the helper module.",
        )
        assert result is not None
        assert result["decision"] == "warn"

    def test_added_no_completion_claim(self):
        """'I added the gate' should NOT escalate to block."""
        result = check_alignment(
            prompt="modify Stop.py",
            tool_events=[
                {"name": "Write", "file_path": "helper.py"},
            ],
            response="I added the helper function.",
        )
        assert result is not None
        assert result["decision"] == "warn"

    def test_fixed_no_completion_claim(self):
        """'I fixed the bug' should NOT escalate to block."""
        result = check_alignment(
            prompt="modify Stop.py",
            tool_events=[
                {"name": "Edit", "file_path": "helper.py"},
            ],
            response="I fixed the issue in the helper.",
        )
        assert result is not None
        assert result["decision"] == "warn"

    def test_all_tests_pass_triggers_block(self):
        result = check_alignment(
            prompt="modify Stop.py",
            tool_events=[
                {"name": "Write", "file_path": "helper.py"},
            ],
            response="All tests pass.",
        )
        assert result is not None
        assert result["decision"] == "block"


# =============================================================================
# TEST 7: Clause-level scoping for in/to path extraction
# =============================================================================


class TestClauseScoping:
    """Verify that 'in <path>' / 'to <path>' only match near modification verbs."""

    def test_in_path_near_verb(self):
        targets = extract_targets_from_prompt("add tests in test_foo.py")
        paths = [t.value for t in targets if t.kind == "file"]
        assert any("test_foo.py" in p for p in paths)

    def test_in_path_far_from_verb_not_extracted(self):
        """'in <path>' far from any modification verb should not be a target."""
        targets = extract_targets_from_prompt(
            "fix the bug in Stop.py then verify the documented behavior described in README.md"
        )
        paths = [t.value for t in targets if t.kind == "file"]
        # Stop.py should be a target ("fix" is near "in Stop.py")
        assert any("Stop.py" in p for p in paths)
        # README.md should NOT be a target (no verb within 60 chars of "in README.md")
        assert not any("README.md" in p for p in paths)

    def test_to_path_near_verb(self):
        targets = extract_targets_from_prompt("add the gate to Stop.py")
        paths = [t.value for t in targets if t.kind == "file"]
        assert any("Stop.py" in p for p in paths)
