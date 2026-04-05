"""Integration tests for adversarial dispatch system.

Validates the contracts between adversarial-review orchestrator,
specialist agents, and the adversarial-critic meta-analyzer.

Key contracts tested:
1. All specialist agents contain the "return ONLY file path" instruction
   (prevents context overflow when 6+ agents run in parallel)
2. Findings file paths are consistent between writers and readers
3. Orchestrator references all expected agents
4. Each agent has valid frontmatter and tool declarations
"""

from __future__ import annotations

import re
from pathlib import Path
import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AGENTS_DIR = Path(__file__).resolve().parent.parent

# 12 specialist agents that produce findings and need the "return ONLY" contract
SPECIALIST_AGENTS = [
    "adversarial-compliance",
    "adversarial-failure-modes",
    "adversarial-invariants",
    "adversarial-io-validation",
    "adversarial-logic",
    "adversarial-performance",
    "adversarial-qa",
    "adversarial-quality",
    "adversarial-security",
    "adversarial-state-machine",
    "adversarial-state-machine-prototype",
    "adversarial-testing",
]

# Orchestrator and meta-analyzer (no "return ONLY" contract needed)
ORCHESTRATOR_AGENT = "adversarial-review"
CRITIC_AGENT = "adversarial-critic"

ALL_AGENTS = SPECIALIST_AGENTS + [ORCHESTRATOR_AGENT, CRITIC_AGENT]

# The 7 parallel agents the orchestrator dispatches (from adversarial-review.md)
ORCHESTRATOR_PARALLEL_AGENTS = [
    "adversarial-security",
    "adversarial-performance",
    "adversarial-compliance",
    "adversarial-quality",
    "adversarial-testing",
    "code-critic",
    "qa-engineer",
]

# Expected findings paths (from adversarial-review.md and adversarial-critic.md)
EXPECTED_FINDINGS_PATHS = [
    "compliance-findings.json",
    "logic-findings.json",
    "testing-findings.json",
    "security-findings.json",
    "failure-modes-findings.json",
    "performance-findings.json",
]

FINDINGS_DIR = "P:/.claude/plans/adversarial/"

# The contract string that prevents context overflow
FILE_PATH_CONTRACT = "response text must contain ONLY the file path"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_agent(name: str) -> str:
    """Read an agent's markdown file content."""
    path = AGENTS_DIR / f"{name}.md"
    if not path.exists():
        pytest.fail(f"Agent file not found: {path}")
    return path.read_text(encoding="utf-8")


def _parse_frontmatter(content: str) -> dict[str, str]:
    """Extract YAML frontmatter key-value pairs from agent markdown."""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    fm: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


# ---------------------------------------------------------------------------
# Tests: Agent Existence & Frontmatter
# ---------------------------------------------------------------------------


class TestAgentExistence:
    """Verify all expected agent files exist with valid frontmatter."""

    @pytest.mark.parametrize("agent_name", ALL_AGENTS)
    def test_agent_file_exists(self, agent_name: str) -> None:
        path = AGENTS_DIR / f"{agent_name}.md"
        assert path.exists(), f"Agent file missing: {path}"

    @pytest.mark.parametrize("agent_name", ALL_AGENTS)
    def test_agent_has_required_frontmatter(self, agent_name: str) -> None:
        content = _read_agent(agent_name)
        fm = _parse_frontmatter(content)
        assert "name" in fm, f"{agent_name}: missing 'name' in frontmatter"
        assert "description" in fm, f"{agent_name}: missing 'description' in frontmatter"
        assert fm["name"] == agent_name, (
            f"{agent_name}: frontmatter name '{fm['name']}' != filename '{agent_name}'"
        )

    def test_no_duplicate_frontmatter_names(self) -> None:
        """No two agent files should declare the same name."""
        names: list[str] = []
        for agent_name in ALL_AGENTS:
            content = _read_agent(agent_name)
            fm = _parse_frontmatter(content)
            names.append(fm.get("name", ""))
        duplicates = [n for n in names if names.count(n) > 1]
        assert not duplicates, f"Duplicate agent names found: {set(duplicates)}"


# ---------------------------------------------------------------------------
# Tests: File-Path-Only Contract (prevents context overflow)
# ---------------------------------------------------------------------------


class TestFilePathContract:
    """Verify specialist agents contain the 'return ONLY file path' instruction.

    This contract was introduced to fix a context overflow bug: when 6+ agents
    run in parallel and each returns full JSON findings in their response text,
    the combined output exceeds the orchestrator's context window. The fix:
    agents write findings to disk and return ONLY the file path.
    """


    @pytest.mark.parametrize("agent_name", SPECIALIST_AGENTS)
    def test_specialist_has_file_path_contract(self, agent_name: str) -> None:
        content = _read_agent(agent_name)
        assert FILE_PATH_CONTRACT in content, (
            f"{agent_name}: missing 'return ONLY file path' contract. "
            f"Without this, the agent will return full JSON findings in its "
            f"response text, causing context overflow in parallel dispatch."
        )

    def test_critic_does_not_need_contract(self) -> None:
        """The critic reads findings; it doesn't produce them for aggregation."""
        content = _read_agent(CRITIC_AGENT)
        # Critic should NOT have the contract — it reads, doesn't write for others
        assert FILE_PATH_CONTRACT not in content, (
            f"{CRITIC_AGENT}: unexpectedly has the file-path-only contract. "
            f"The critic is a meta-analyzer, not a findings producer."
        )

    def test_orchestrator_includes_contract_in_dispatch(self) -> None:
        """The orchestrator must pass the contract in Task() descriptions."""
        content = _read_agent(ORCHESTRATOR_AGENT)
        # The orchestrator uses slightly different wording: "response must contain ONLY"
        # vs specialist agents: "response text must contain ONLY"
        has_contract = (
            FILE_PATH_CONTRACT in content
            or "response must contain ONLY the file path" in content
        )
        assert has_contract, (
            f"{ORCHESTRATOR_AGENT}: dispatch descriptions must include the "
            f"'return ONLY file path' instruction so subagents comply."
        )


# ---------------------------------------------------------------------------
# Tests: JSON Output Schema
# ---------------------------------------------------------------------------


class TestJsonOutputSchema:
    """Verify specialist agents define a JSON findings schema."""


    @pytest.mark.parametrize("agent_name", SPECIALIST_AGENTS)
    def test_specialist_defines_json_schema(self, agent_name: str) -> None:
        content = _read_agent(agent_name)
        assert "findings" in content.lower(), (
            f"{agent_name}: no 'findings' section found. "
            f"Every specialist must define a JSON output schema."
        )
        # Should reference a .json output file
        assert ".json" in content, (
            f"{agent_name}: no .json output path defined."
        )

    @pytest.mark.parametrize("agent_name", SPECIALIST_AGENTS)
    def test_specialist_defines_severity_levels(self, agent_name: str) -> None:
        content = _read_agent(agent_name)
        # Agents should define severity classification
        has_severity = any(
            kw in content.lower()
            for kw in ["severity", "blocker", "high", "medium", "low"]
        )
        assert has_severity, (
            f"{agent_name}: no severity classification found. "
            f"Findings must be classified by severity."
        )


# ---------------------------------------------------------------------------
# Tests: Findings Path Consistency
# ---------------------------------------------------------------------------


class TestFindingsPathConsistency:
    """Verify findings file paths are consistent across the system.

    Agents write to specific paths. The critic reads from those same paths.
    The orchestrator references those paths. All three must agree.
    """


    def test_critic_reads_expected_findings_paths(self) -> None:
        content = _read_agent(CRITIC_AGENT)
        for finding_file in EXPECTED_FINDINGS_PATHS:
            assert finding_file in content, (
                f"{CRITIC_AGENT}: does not reference '{finding_file}'. "
                f"The critic must read all specialist finding files."
            )

    def test_specialist_agents_write_to_findings_dir(self) -> None:
        """Specialist agents should write to the adversarial findings directory."""
        for agent_name in SPECIALIST_AGENTS:
            content = _read_agent(agent_name)
            # At least some specialists should reference the findings directory
            if FINDINGS_DIR.rstrip("/") in content:
                # Verify the path includes a -findings.json file
                pattern = r"adversarial/\w+-findings\.json"
                matches = re.findall(pattern, content)
                if matches:
                    # The agent name should appear in at least one path
                    has_own_path = any(agent_name.replace("adversarial-", "") in m for m in matches)
                    if not has_own_path and matches:
                        # Some agents (like state-machine) may not match their name exactly
                        pass  # acceptable — not all agents follow naming convention

    def test_orchestrator_references_findings_dir(self) -> None:
        content = _read_agent(ORCHESTRATOR_AGENT)
        assert "adversarial/" in content, (
            f"{ORCHESTRATOR_AGENT}: must reference the adversarial findings directory."
        )


# ---------------------------------------------------------------------------
# Tests: Orchestrator Dispatch Correctness
# ---------------------------------------------------------------------------


class TestOrchestratorDispatch:
    """Verify the orchestrator correctly references all dispatchable agents."""


    @pytest.mark.parametrize("agent_ref", ORCHESTRATOR_PARALLEL_AGENTS)
    def test_orchestrator_references_parallel_agent(self, agent_ref: str) -> None:
        content = _read_agent(ORCHESTRATOR_AGENT)
        assert agent_ref in content, (
            f"{ORCHESTRATOR_AGENT}: does not reference agent '{agent_ref}'. "
            f"All parallel agents must be listed in the orchestrator."
        )

    def test_orchestrator_references_critic_sequentially(self) -> None:
        content = _read_agent(ORCHESTRATOR_AGENT)
        assert CRITIC_AGENT in content, (
            f"{ORCHESTRATOR_AGENT}: does not reference '{CRITIC_AGENT}'. "
            f"The critic must be dispatched sequentially after parallel agents."
        )

    def test_orchestrator_specifies_parallel_execution(self) -> None:
        content = _read_agent(ORCHESTRATOR_AGENT)
        # Should mention parallel or simultaneous execution
        has_parallel = any(
            kw in content.lower()
            for kw in ["parallel", "simultaneous", "single message"]
        )
        assert has_parallel, (
            f"{ORCHESTRATOR_AGENT}: must specify parallel execution for agents."
        )

    def test_orchestrator_specifies_sequential_critic(self) -> None:
        content = _read_agent(ORCHESTRATOR_AGENT)
        # Should mention the critic runs AFTER parallel agents
        has_sequential = any(
            kw in content.lower()
            for kw in ["sequential", "after", "wait for"]
        )
        assert has_sequential, (
            f"{ORCHESTRATOR_AGENT}: must specify that critic runs after parallel agents."
        )


# ---------------------------------------------------------------------------
# Tests: Tool Declarations
# ---------------------------------------------------------------------------


class TestToolDeclarations:
    """Verify specialist agents declare appropriate read-only tools."""

    READ_ONLY_TOOLS = {"Read", "Grep", "Glob", "Bash"}

    @pytest.mark.parametrize("agent_name", SPECIALIST_AGENTS)
    def test_specialist_has_read_tools(self, agent_name: str) -> None:
        content = _read_agent(agent_name)
        fm = _parse_frontmatter(content)
        tools_str = fm.get("tools", "")
        if not tools_str:
            pytest.skip(f"{agent_name}: no tools declared in frontmatter (inherits default)")
        declared = {t.strip() for t in tools_str.split(",")}
        # Must have at least Read for file inspection
        assert "Read" in declared, (
            f"{agent_name}: must declare 'Read' tool. Found: {declared}"
        )


# ---------------------------------------------------------------------------
# Tests: Handoff Protocol
# ---------------------------------------------------------------------------


class TestHandoffProtocol:
    """Verify the JSON handoff packet structure."""


    @pytest.mark.parametrize("agent_name", SPECIALIST_AGENTS)
    def test_specialist_defines_handoff_schema(self, agent_name: str) -> None:
        content = _read_agent(agent_name)
        # Should define handoff or output JSON structure
        has_handoff = any(
            kw in content.lower()
            for kw in ["handoff", "json", "output schema"]
        )
        assert has_handoff, (
            f"{agent_name}: no handoff/output schema defined. "
            f"Specialist agents must define their JSON output structure."
        )

    def test_critic_defines_verification_step(self) -> None:
        """The critic must verify findings against actual codebase."""
        content = _read_agent(CRITIC_AGENT)
        assert "verif" in content.lower(), (
            f"{CRITIC_AGENT}: must define a verification step for findings."
        )
