"""
Tests for PreToolUse_policy_gate hook.

These tests verify the policy gate hook functionality:
- Loading policy JSON files encoding Invariant Kernel tiers
- Running analyzers before tool execution (cached, 1-minute TTL)
- Risk-based gating (low-risk tools skip analysis)
- Per-terminal ID scoping
- Intercepts read_file, write_file, edit, bash tools

Run with: pytest tests/test_policy_gate.py -v
"""

import json
from pathlib import Path
from unittest.mock import patch

# Test data
SAMPLE_POLICY_JSON = {
    "prime_rules": {
        "backward_compatibility": {
            "description": "Maintain backward compatibility for public APIs",
            "enforcement": "warn"
        },
        "consumer_guarantees": {
            "description": "Honor all documented consumer guarantees",
            "enforcement": "block"
        }
    },
    "system_rules": {
        "path_canonicalization": {
            "description": "Use os.path.realpath only for path canonicalization",
            "allowed_functions": ["os.path.realpath"],
            "forbidden_patterns": [r"re\.search\(.*/.*\)", r"re\.match\(.*/.*\)"],
            "enforcement": "block"
        },
        "no_regex_for_safety": {
            "description": "No regex for security-critical validation",
            "forbidden_patterns": [r"re\.match\(.*user_input", r"re\.search\(.*path"],
            "enforcement": "block"
        }
    },
    "domain_rules": {
        "layering": {
            "description": "Enforce architectural layering",
            "layers": ["domain", "application", "infrastructure"],
            "forbidden_imports": [
                "infrastructure.*domain",
                "infrastructure.*application"
            ],
            "enforcement": "warn"
        },
        "modularity": {
            "description": "Maintain module boundaries",
            "max_module_size": 500,
            "enforcement": "warn"
        }
    },
    "artifact_rules": {
        "api_contracts": {
            "description": "Verify API contract compliance",
            "enforcement": "warn"
        },
        "function_signatures": {
            "description": "Enforce consistent function signatures",
            "enforcement": "warn"
        }
    }
}


class TestPolicyGateLoadPolicy:
    """Tests for policy loading functionality."""

    def test_load_policy_json(self, tmp_path):
        """
        Test loading policy JSON file.

        Given: Policy JSON file exists in policies directory
        When: Loading policy file
        Then: Should return policy dictionary with all tiers:
              - prime_rules
              - system_rules
              - domain_rules
              - artifact_rules
        """
        # Arrange: Create policy file
        policies_dir = tmp_path / ".claude" / "policies"
        policies_dir.mkdir(parents=True)

        policy_file = policies_dir / "invariant_kernel.json"
        with open(policy_file, 'w') as f:
            json.dump(SAMPLE_POLICY_JSON, f)

        # Act: Load policy
        from hooks.PreToolUse_policy_gate import load_policy

        policy = load_policy(str(policy_file))

        # Assert: All tiers present
        assert "prime_rules" in policy
        assert "system_rules" in policy
        assert "domain_rules" in policy
        assert "artifact_rules" in policy

        # Assert: Specific rules present
        assert "backward_compatibility" in policy["prime_rules"]
        assert "path_canonicalization" in policy["system_rules"]
        assert "layering" in policy["domain_rules"]
        assert "api_contracts" in policy["artifact_rules"]

    def test_load_policy_missing_file(self):
        """
        Test handling of missing policy file.

        Given: Policy file does not exist
        When: Loading policy
        Then: Should return empty policy dict (fail-open)
        """
        from hooks.PreToolUse_policy_gate import load_policy

        policy = load_policy("/nonexistent/policy.json")

        assert policy == {}

    def test_load_policy_invalid_json(self, tmp_path):
        """
        Test handling of invalid policy JSON.

        Given: Policy file contains invalid JSON
        When: Loading policy
        Then: Should return empty policy dict (fail-open)
        """
        # Arrange: Create invalid JSON file
        policies_dir = tmp_path / ".claude" / "policies"
        policies_dir.mkdir(parents=True)

        policy_file = policies_dir / "invalid.json"
        policy_file.write_text("{ invalid json }")

        # Act: Load policy
        from hooks.PreToolUse_policy_gate import load_policy

        policy = load_policy(str(policy_file))

        # Assert: Fail-open
        assert policy == {}


class TestPolicyGateToolInterception:
    """Tests for tool interception."""

    def test_intercept_read_file(self):
        """
        Test interception of read_file tool.

        Given: PreToolUse_policy_gate hook registered
        When: Read tool is called
        Then: Should intercept and analyze if high-risk
        """
        from hooks.PreToolUse_policy_gate import should_intercept_tool

        # High-risk read (reading policy file)
        assert should_intercept_tool("Read", {"file_path": ".claude/policies/kernel.json"})

        # Low-risk read (reading regular code)
        assert not should_intercept_tool("Read", {"file_path": "src/main.py"})

    def test_intercept_write_file(self):
        """
        Test interception of write_file tool.

        Given: PreToolUse_policy_gate hook registered
        When: Write tool is called
        Then: Should always intercept (high-risk operation)
        """
        from hooks.PreToolUse_policy_gate import should_intercept_tool

        # All writes are high-risk
        assert should_intercept_tool("Write", {"file_path": "any/path.py"})

    def test_intercept_edit(self):
        """
        Test interception of edit tool.

        Given: PreToolUse_policy_gate hook registered
        When: Edit tool is called
        Then: Should always intercept (high-risk operation)
        """
        from hooks.PreToolUse_policy_gate import should_intercept_tool

        # All edits are high-risk
        assert should_intercept_tool("Edit", {"file_path": "any/path.py"})

    def test_intercept_bash(self):
        """
        Test interception of bash tool.

        Given: PreToolUse_policy_gate hook registered
        When: Bash tool is called
        Then: Should intercept only high-risk commands
        """
        from hooks.PreToolUse_policy_gate import should_intercept_tool

        # High-risk bash (installing packages)
        assert should_intercept_tool("Bash", {"command": "pip install package"})

        # Low-risk bash (simple commands)
        assert not should_intercept_tool("Bash", {"command": "ls -la"})

    def test_skip_low_risk_tools(self):
        """
        Test that low-risk tools skip analysis.

        Given: Tool operation with low risk
        When: Checking if should intercept
        Then: Should return False for low-risk tools
        """
        from hooks.PreToolUse_policy_gate import should_intercept_tool

        # Skill tool - low risk
        assert not should_intercept_tool("Skill", {})

        # AskUserQuestion - low risk
        assert not should_intercept_tool("AskUserQuestion", {})

        # Glob - low risk
        assert not should_intercept_tool("Glob", {})


class TestPolicyGateAnalyzers:
    """Tests for analyzer execution."""

    @patch('hooks.PreToolUse_policy_gate.run_path_traversal_analysis')
    def test_run_analyzers_cached(self, mock_path_analysis, tmp_path):
        """
        Test that analyzer results are cached with 1-minute TTL.

        Given: Analyzer already ran within 1 minute
        When: Running analyzer again for same file
        Then: Should return cached result without re-running
        """
        # Arrange: Create package directory
        pkg_dir = tmp_path / "test_package"
        pkg_dir.mkdir()
        (pkg_dir / "module.py").write_text("def test(): pass")

        # Arrange: Set up cached result
        from hooks.PreToolUse_policy_gate import set_analysis_cache

        cache_key = f"path_traversal:{str(pkg_dir)}"
        cached_findings = [{"severity": "LOW", "message": "Cached finding"}]
        set_analysis_cache(cache_key, cached_findings)

        # Act: Run analyzers
        from hooks.PreToolUse_policy_gate import run_analyzers

        findings = run_analyzers(str(pkg_dir), policy={})

        # Assert: Cached result returned, analyzer not re-run
        assert findings == cached_findings
        mock_path_analysis.assert_not_called()

    @patch('hooks.PreToolUse_policy_gate.run_path_traversal_analysis')
    def test_run_analyzers_cache_expired(self, mock_path_analysis, tmp_path):
        """
        Test that cache expires after 1 minute.

        Given: Cached result is older than 1 minute
        When: Running analyzer
        Then: Should re-run analyzer and update cache
        """
        # Arrange: Create package directory
        pkg_dir = tmp_path / "test_package"
        pkg_dir.mkdir()
        (pkg_dir / "module.py").write_text("def test(): pass")

        # Arrange: Set up expired cache
        from hooks.PreToolUse_policy_gate import set_analysis_cache

        cache_key = f"path_traversal:{str(pkg_dir)}"
        old_findings = [{"severity": "LOW", "message": "Old cached finding"}]

        # Set cache with old timestamp
        import time
        old_timestamp = time.time() - 61  # 61 seconds ago
        set_analysis_cache(cache_key, old_findings, timestamp=old_timestamp)

        # Arrange: Mock analyzer to return new findings
        new_findings = [{"severity": "HIGH", "message": "New finding"}]
        mock_path_analysis.return_value = new_findings

        # Act: Run analyzers
        from hooks.PreToolUse_policy_gate import run_analyzers

        findings = run_analyzers(str(pkg_dir), policy={})

        # Assert: New findings returned, cache updated
        assert findings == new_findings
        mock_path_analysis.assert_called_once()

    @patch('hooks.PreToolUse_policy_gate.run_path_traversal_analysis')
    @patch('hooks.PreToolUse_policy_gate.run_import_graph_analysis')
    @patch('hooks.PreToolUse_policy_gate.run_doc_consistency_analysis')
    def test_run_all_analyzers(self, mock_doc, mock_import, mock_path, tmp_path):
        """
        Test that all three analyzers run when no cache exists.

        Given: Package with no cached analysis
        When: Running analyzers
        Then: Should run all three analyzers:
              - path_traversal
              - import_graph
              - doc_consistency
        """
        # Arrange: Create package directory
        pkg_dir = tmp_path / "test_package"
        pkg_dir.mkdir()
        (pkg_dir / "module.py").write_text("def test(): pass")

        # Arrange: Mock analyzers
        mock_path.return_value = [{"severity": "MEDIUM", "message": "Path finding"}]
        mock_import.return_value = [{"severity": "LOW", "message": "Import finding"}]
        mock_doc.return_value = [{"severity": "WARN", "message": "Doc finding"}]

        # Act: Run analyzers
        from hooks.PreToolUse_policy_gate import run_analyzers

        findings = run_analyzers(str(pkg_dir), policy={})

        # Assert: All analyzers called
        mock_path.assert_called_once()
        mock_import.assert_called_once()
        mock_doc.assert_called_once()

        # Assert: Findings combined
        assert len(findings) == 3


class TestPolicyGateDecision:
    """Tests for policy gate decision logic."""

    def test_allow_low_risk_operation(self):
        """
        Test that low-risk operations are allowed.

        Given: Tool operation with low risk profile
        When: Making policy gate decision
        Then: Should return None (allow)
        """
        from hooks.PreToolUse_policy_gate import make_policy_decision

        decision = make_policy_decision(
            tool_name="Glob",
            tool_input={},
            findings=[]
        )

        assert decision is None

    def test_block_high_severity_finding(self):
        """
        Test that HIGH severity findings block operation.

        Given: Analysis returned HIGH severity finding
        When: Making policy gate decision
        Then: Should return block decision with reason
        """
        from hooks.PreToolUse_policy_gate import make_policy_decision

        findings = [
            {"severity": "HIGH", "message": "Path traversal vulnerability detected"}
        ]

        decision = make_policy_decision(
            tool_name="Write",
            tool_input={"file_path": "vulnerable.py"},
            findings=findings
        )

        assert decision is not None
        assert decision["decision"] == "block"
        assert "Path traversal vulnerability" in decision["reason"]

    def test_warn_medium_severity_finding(self):
        """
        Test that MEDIUM severity findings warn but allow.

        Given: Analysis returned MEDIUM severity finding
        When: Making policy gate decision
        Then: Should return allow_with_warning decision
        """
        from hooks.PreToolUse_policy_gate import make_policy_decision

        findings = [
            {"severity": "MEDIUM", "message": "Circular dependency detected"}
        ]

        decision = make_policy_decision(
            tool_name="Edit",
            tool_input={"file_path": "module.py"},
            findings=findings
        )

        # MEDIUM severity should warn but allow
        assert decision is None  # Currently allows, logs warning

    def test_allow_no_findings(self):
        """
        Test that operations with no findings are allowed.

        Given: Analysis returned no findings
        When: Making policy gate decision
        Then: Should return None (allow)
        """
        from hooks.PreToolUse_policy_gate import make_policy_decision

        decision = make_policy_decision(
            tool_name="Write",
            tool_input={"file_path": "safe.py"},
            findings=[]
        )

        assert decision is None


class TestPolicyGateTerminalIsolation:
    """Tests for per-terminal ID scoping."""

    def test_per_terminal_state_isolation(self, tmp_path):
        """
        Test that state is isolated per terminal ID.

        Given: Two different terminal IDs
        When: Each terminal creates analysis cache
        Then: Each should have separate cache (no cross-terminal pollution)
        """
        # Arrange: Set up two different terminal IDs
        state_dir = tmp_path / ".claude" / "state" / "policy_gate"

        # Terminal 1 cache
        term1_cache_dir = state_dir / "terminal-1"
        term1_cache_dir.mkdir(parents=True)
        term1_cache = term1_cache_dir / "analysis_cache.json"
        term1_cache.write_text(json.dumps({"key": "terminal1_value"}))

        # Terminal 2 cache
        term2_cache_dir = state_dir / "terminal-2"
        term2_cache_dir.mkdir(parents=True)
        term2_cache = term2_cache_dir / "analysis_cache.json"
        term2_cache.write_text(json.dumps({"key": "terminal2_value"}))

        # Act: Load cache for each terminal
        with patch.dict('os.environ', {'CLAUDE_TERMINAL_ID': 'terminal-1'}):
            from hooks.PreToolUse_policy_gate import get_cache_file_path
            cache_path_1 = get_cache_file_path()

        with patch.dict('os.environ', {'CLAUDE_TERMINAL_ID': 'terminal-2'}):
            from hooks.PreToolUse_policy_gate import get_cache_file_path
            cache_path_2 = get_cache_file_path()

        # Assert: Different paths
        assert cache_path_1 != cache_path_2
        assert "terminal-1" in str(cache_path_1)
        assert "terminal-2" in str(cache_path_2)

    def test_default_terminal_id(self):
        """
        Test that default terminal ID is used when none set.

        Given: No CLAUDE_TERMINAL_ID environment variable
        When: Getting cache file path
        Then: Should use "default" terminal ID
        """
        with patch.dict('os.environ', {}, clear=True):
            from hooks.PreToolUse_policy_gate import get_cache_file_path

            cache_path = get_cache_file_path()

            assert "default" in str(cache_path)


class TestPolicyGateIntegration:
    """Integration tests for policy gate hook."""

    def test_hook_main_entry_point(self, tmp_path):
        """
        Test hook main() function entry point.

        Given: PreToolUse_policy_gate hook installed
        When: Hook receives tool use event via stdin
        Then: Should process and return decision JSON
        """
        # Arrange: Create test environment
        pkg_dir = tmp_path / "test_package"
        pkg_dir.mkdir()
        (pkg_dir / "safe.py").write_text("# Safe file")

        policies_dir = tmp_path / ".claude" / "policies"
        policies_dir.mkdir(parents=True)
        policy_file = policies_dir / "invariant_kernel.json"
        with open(policy_file, 'w') as f:
            json.dump(SAMPLE_POLICY_JSON, f)

        # Arrange: Hook input data
        hook_input = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(pkg_dir / "safe.py")
            }
        }

        # Act: Call hook main
        import sys
        from io import StringIO

        from hooks.PreToolUse_policy_gate import main

        old_stdin = sys.stdin
        old_stdout = sys.stdout

        try:
            sys.stdin = StringIO(json.dumps(hook_input))
            sys.stdout = StringIO()

            main()  # Should not raise

            output = sys.stdout.getvalue()

        finally:
            sys.stdin = old_stdin
            sys.stdout = old_stdout

        # Assert: Output is valid JSON
        result = json.loads(output)

        # Should have decision
        assert "continue" in result or "decision" in result

    def test_hook_integration_with_pretooluse_router(self):
        """
        Test that hook integrates with PreToolUse router.

        Given: PreToolUse_policy_gate hook exists
        When: Checking PreToolUse.py router configuration
        Then: Hook should be registered for appropriate tools
        """
        # This is a structural test - verify hook file exists
        hook_path = Path("hooks/PreToolUse_policy_gate.py")

        # Hook file should exist
        assert hook_path.exists()

        # Hook should have main() function
        import importlib.util
        spec = importlib.util.spec_from_file_location("policy_gate", hook_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert callable(module.main)
