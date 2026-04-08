"""GTO v3 Orchestrator - Main entry point for gap analysis.

This module coordinates all detectors, subagents, and produces the final output.
It implements the three-layer architecture:
- Layer 1: Python Deterministic (detectors)
- Layer 2: Agents/AI Reasoning (subagents)
- Layer 3: Claude Orchestrator (this module)
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Import GTO library components - handle both package and direct import
try:
    from .lib import (
        ConsolidatedResults,
        Gap,
        build_initial_results,
        calculate_health,
        check_chain_integrity,
        check_entry_points,
        check_skill_health,
        check_viability,
        detect_git_context,
        detect_session_goal,
        detect_task_list_gaps,
        detect_unfinished_business,
        find_gaps,
        format_recommended_next_steps,
        format_rsn_from_gaps,
        get_gap_decay_metrics,
        get_state_manager,
        track_gap_resolutions,
    )
    from .lib.session_memoizer import SessionMemoizer, _build_chain_signature
except ImportError:
    # When imported directly (e.g., in tests), import from lib
    from lib import (
        ConsolidatedResults,
        Gap,
        build_initial_results,
        calculate_health,
        check_chain_integrity,
        check_entry_points,
        check_skill_health,
        check_viability,
        detect_git_context,
        detect_session_goal,
        detect_session_outcomes,
        detect_suspicion,
        detect_task_list_gaps,
        detect_unfinished_business,
        find_gaps,
        format_rsn_from_gaps,
        get_gap_decay_metrics,
        get_state_manager,
        track_gap_resolutions,
    )
    from lib.session_memoizer import SessionMemoizer, _build_chain_signature

# Import skill coverage detector - handle both package and direct import
try:
    from .lib.skill_coverage_detector import detect_skill_coverage
except ImportError:
    # When imported directly (e.g., in tests), import from lib
    from lib.skill_coverage_detector import detect_skill_coverage

# Import session chain analyzer - handle both package and direct import
try:
    from .lib.session_chain_analyzer import ChainAnalysisResult, SessionChainAnalyzer
except ImportError:
    from lib.session_chain_analyzer import ChainAnalysisResult, SessionChainAnalyzer


import hashlib
import logging

logger = logging.getLogger(__name__)


def _auto_detect_transcript_path() -> Path | None:
    """Auto-detect the most recent session transcript file.

    Searches ~/.claude/projects/*.jsonl for the most recently modified file.
    This provides "best outcomes by default" - GTO always analyzes chat history
    without requiring explicit --transcript parameter.

    Returns:
        Path to the most recent transcript, or None if none found
    """
    try:
        sessions_dir = Path.home() / ".claude" / "projects"
        if not sessions_dir.exists():
            return None
        files = sorted(
            sessions_dir.glob("*.jsonl"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if files:
            logger.info("Auto-detected transcript: %s", files[0])
            return files[0]
        logger.debug("No session files found for auto-detection")
        return None
    except Exception as e:
        logger.warning("Failed to auto-detect transcript: %s", e)
        return None


def _get_transcript_fingerprint(transcript_path: Path | None) -> str | None:
    """Get a fingerprint for incremental analysis caching.

    Uses file size + modification time for quick change detection.
    This enables efficient re-analysis when transcript hasn't changed.

    Args:
        transcript_path: Path to transcript file

    Returns:
        Fingerprint string or None if no path
    """
    if not transcript_path or not transcript_path.exists():
        return None
    try:
        stat = transcript_path.stat()
        # Use size + mtime for quick fingerprint
        fingerprint = f"{stat.st_size}_{int(stat.st_mtime)}"
        return hashlib.md5(fingerprint.encode()).hexdigest()[:16]
    except OSError:
        return None


def _get_default_terminal_id() -> str:
    """Auto-detect terminal ID without importing hook_base (namespace conflict).

    Priority:
    1. CLAUDE_TERMINAL_ID env var (highest — wired to canonical)
    2. canonical_terminal_id() from core.terminal_id (collision-resistant)
    """
    import os
    from pathlib import Path

    # Priority 1: explicit env override
    if value := os.environ.get("CLAUDE_TERMINAL_ID", "").strip():
        return value

    # Priority 2: use canonical_terminal_id() from search-research
    try:
        import sys

        # P:/packages/search-research — resolved relative to this file's location
        search_research_root = (
            Path(__file__).parent.parent.parent.parent / "packages" / "search-research"
        )
        if str(search_research_root) not in sys.path:
            sys.path.insert(0, str(search_research_root))
        from core.terminal_id import canonical_terminal_id

        return canonical_terminal_id()
    except Exception:
        return "unknown"


@dataclass
class OrchestratorConfig:
    """Configuration for GTO orchestrator."""

    project_root: Path | None = None
    terminal_id: str = field(default_factory=_get_default_terminal_id)
    transcript_path: Path | None = None
    enable_subagents: bool = False  # Disabled: gap types route to dedicated skills (/qa, /docs, /critique, /deps)
    enable_health_check: bool = True
    enable_correctness: bool = True
    correctness_modes: list[str] = field(
        default_factory=lambda: ["logic", "quality", "code-critic"]
    )
    state_dir: Path | None = None
    verbose: bool = False


@dataclass
class OrchestratorResult:
    """Result from GTO orchestrator."""

    success: bool
    viability_passed: bool
    results: ConsolidatedResults | None
    health_report: dict[str, Any] | None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "viability_passed": self.viability_passed,
            "results": self.results.to_dict() if self.results else None,
            "health_report": self.health_report,
            "error": self.error,
            "metadata": self.metadata,
        }


class GTOOrchestrator:
    """
    Main orchestrator for GTO gap analysis.

    Coordinates all detectors and subagents to produce comprehensive
    gap analysis results.
    """

    def __init__(self, config: OrchestratorConfig) -> None:
        """Initialize orchestrator.

        Args:
            config: Orchestrator configuration
        """
        self.config = config
        if config.project_root:
            self.project_root = Path(config.project_root).resolve()
        else:
            cwd = Path.cwd().resolve()
            logger.warning(
                "No --project-root specified. Using cwd as project_root: %s\n"
                "Results may be unexpected if cwd is not a valid target.\n"
                "Specify --project-root explicitly for accurate analysis.",
                cwd,
            )
            self.project_root = cwd

        # AUTO-DETECT transcript path when not provided
        # This ensures "best outcomes by default" - GTO always analyzes chat history
        if not self.config.transcript_path:
            auto_detected = _auto_detect_transcript_path()
            if auto_detected:
                logger.info("Auto-detected transcript: %s", auto_detected)
                # Update config with auto-detected path
                self.config.transcript_path = auto_detected
            else:
                logger.debug("No transcript auto-detected - running without chat history analysis")

        # Get state manager for multi-terminal isolation
        self.state_manager = get_state_manager(
            self.project_root,
            config.terminal_id,
            config.state_dir,
        )

        # Load previous state if available
        self.previous_state = self.state_manager.load()

        # Cache transcript fingerprint for incremental analysis
        self._transcript_fingerprint = _get_transcript_fingerprint(self.config.transcript_path)

    def run(self) -> OrchestratorResult:
        """
        Run full GTO analysis.

        Returns:
            OrchestratorResult with analysis results
        """
        metadata: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "terminal_id": self.config.terminal_id,
        }

        try:
            # Step 1: Viability Gate (P0)
            # Pass transcript_path from config so viability gate can find actual transcript files
            viability_result = check_viability(self.project_root, self.config.transcript_path)
            metadata["viability_check"] = {
                "is_viable": viability_result.is_viable,
                "failure_reason": viability_result.failure_reason,
            }

            if not viability_result.is_viable:
                return OrchestratorResult(
                    success=False,
                    viability_passed=False,
                    results=None,
                    health_report=None,
                    error=f"Viability check failed: {viability_result.failure_reason}",
                    metadata=metadata,
                )

            # Step 1.5: Git context detection (informational - doesn't block)
            git_context = detect_git_context(self.project_root)
            metadata["git_context"] = {
                "branch": git_context.branch,
                "branch_display": git_context.branch_display,
                "is_detached": git_context.is_detached,
                "is_worktree": git_context.is_worktree,
                "worktree_count": git_context.worktree_count,
                "error": git_context.error,
            }

            # Step 2: Run all detectors (P2)
            detector_results = self._run_detectors()
            # Note: Not storing detector_results in metadata to avoid JSON serialization issues
            # with complex dataclass objects (CodeMarker, TestGap, etc.)

            # Surface session goal prominently in output
            session_goal_result = detector_results.get("session_goal")
            if session_goal_result is not None:
                metadata["session_goal"] = {
                    "goal": getattr(session_goal_result, "session_goal", None),
                    "confidence": getattr(session_goal_result, "confidence", 0.0),
                    "source_turn": getattr(session_goal_result, "source_turn", None),
                }

            # Step 2.5: Session chain analysis for question-style queries (TASK-003)
            # Detect question-style intent from transcript and run LLM-powered chain analysis
            chain_analysis = self._run_session_chain_analysis(detector_results, session_goal_result)
            if chain_analysis is not None:
                metadata["chain_analysis"] = {
                    "focus": chain_analysis.focus,
                    "phase": chain_analysis.phase,
                    "next_steps": chain_analysis.next_steps,
                    "confidence": chain_analysis.confidence,
                    "error": chain_analysis.error,
                    "transcripts_processed": chain_analysis.transcripts_processed,
                }

            # Step 3: Run subagents (P2)
            subagent_results = self._run_subagents()
            metadata["subagent_results"] = subagent_results

            # Step 4: Build consolidated results (P1)
            results = build_initial_results(detector_results, self.project_root)

            # Merge subagent results
            if "gap_finder" in subagent_results:
                for gap_data in subagent_results["gap_finder"]:
                    gap = Gap(
                        gap_id=gap_data["id"],
                        type=gap_data["type"],
                        severity=gap_data["severity"],
                        message=gap_data["message"],
                        file_path=gap_data.get("file_path"),
                        line_number=gap_data.get("line_number"),
                        source="GapFinderSubagent",
                        confidence=gap_data.get("confidence", 0.8),
                        effort_estimate_minutes=gap_data.get("effort_estimate_minutes", 5),
                        theme=gap_data.get("theme"),
                    )
                    results.gaps.append(gap)

            # Step 3.5: Correctness analysis
            if self.config.enable_correctness:
                correctness_results = self._run_correctness_subagents()
                for agent_name, gaps in correctness_results.items():
                    for gap in gaps:
                        gap.source = f"adversarial-{agent_name}"
                        results.gaps.append(gap)
                logger.info(
                    "Merged correctness gaps: %s",
                    {k: len(v) for k, v in correctness_results.items()},
                )

            # Update counts after merging
            results.total_gap_count = len(results.gaps)
            results.critical_count = sum(1 for g in results.gaps if g.severity == "critical")
            results.high_count = sum(1 for g in results.gaps if g.severity == "high")
            results.medium_count = sum(1 for g in results.gaps if g.severity == "medium")
            results.low_count = sum(1 for g in results.gaps if g.severity == "low")

            # Apply recurrence tracking (convert Gap objects to dicts, then back)
            gaps_as_dicts = [gap.to_dict() for gap in results.gaps]
            updated_gaps_as_dicts = self.state_manager.update_gap_recurrence(gaps_as_dicts)
            results.gaps = [Gap.from_dict(g) for g in updated_gaps_as_dicts]

            # Track gap resolutions for impact-aware prioritization
            # This records which gaps were resolved and credits the running skill
            target_key = str(self.project_root)
            resolution_result = track_gap_resolutions(
                current_gaps=gaps_as_dicts,
                target_key=target_key,
                terminal_id=self.config.terminal_id,
                project_root=self.project_root,
            )
            metadata["resolution_result"] = {
                "resolved_count": resolution_result.resolved_count,
                "new_count": resolution_result.new_count,
                "credited_skill": resolution_result.credited_skill,
            }

            # Compute gap decay metrics for recurrence signal
            decay_metrics = get_gap_decay_metrics(target_key)
            if decay_metrics:
                metadata["gap_decay_metrics"] = {
                    gap_type: {
                        "occurrences": m.occurrences,
                        "first_seen": m.first_seen,
                        "last_seen": m.last_seen,
                        "days_span": m.days_span,
                        "verified_count": m.verified_count,
                        "failed_count": m.failed_count,
                    }
                    for gap_type, m in decay_metrics.items()
                }

            # Step 5: Health check (optional)
            health_report = None
            if self.config.enable_health_check:
                health = calculate_health(self.project_root)
                health_report = health.to_dict()
                metadata["health_report"] = health_report

            # Step 6: Save state
            current_state = self.state_manager.create_state(
                session_id=metadata["timestamp"],
                gaps=[g.to_dict() for g in results.gaps],
                metadata=metadata,
            )
            self.state_manager.save(current_state)

            # Step 7: Append to history
            self.state_manager.append_history(
                {
                    "run_summary": "GTO analysis completed",
                    "gap_count": results.total_gap_count,
                    "health_score": health_report.get("overall_score") if health_report else None,
                }
            )

            return OrchestratorResult(
                success=True,
                viability_passed=True,
                results=results,
                health_report=health_report,
                error=None,
                metadata=metadata,
            )

        except Exception as e:
            return OrchestratorResult(
                success=False,
                viability_passed=False,
                results=None,
                health_report=None,
                error=f"Orchestrator error: {e}",
                metadata=metadata,
            )

    def _run_detectors(self) -> dict[str, Any]:
        """Run all deterministic detectors.

        Returns:
            Dictionary of detector results
        """
        results: dict[str, Any] = {}

        # Chain integrity - pass empty list since we don't have transcript chain paths
        # (transcript paths are for handoff chains, not project analysis)
        results["chain_integrity"] = check_chain_integrity([])

        # Session goal (if transcript available)
        if self.config.transcript_path:
            results["session_goal"] = detect_session_goal(self.config.transcript_path)
        else:
            results["session_goal"] = None

        # Unfinished business (from previous state)
        if self.previous_state and self.config.transcript_path:
            results["unfinished_business"] = detect_unfinished_business(
                self.config.transcript_path,
                self.project_root,
            )
        else:
            results["unfinished_business"] = None

        # Session outcomes (if transcript available)
        if self.config.transcript_path:
            results["session_outcomes"] = detect_session_outcomes(
                self.config.transcript_path,
                self.config.terminal_id,
            )
        else:
            results["session_outcomes"] = None

        # Suspicion detection (if transcript available)
        if self.config.transcript_path:
            results["suspicion"] = detect_suspicion(
                self.config.transcript_path,
                self.config.terminal_id,
            )
        else:
            results["suspicion"] = None

        # Task list gaps (pending CRIT items from shared task list)
        results["task_list"] = detect_task_list_gaps(self.project_root)

        # Skill health
        results["skill_health"] = check_skill_health(self.project_root)

        # Entry point validation (check SKILL.md references exist)
        results["entry_points"] = check_entry_points(self.project_root)

        return results

    def _run_subagents(self) -> dict[str, Any]:
        """Run all AI subagents.

        Returns:
            Dictionary of subagent results
        """
        results: dict[str, Any] = {}

        if not self.config.enable_subagents:
            return results

        # Gap finder subagent
        try:
            gap_result = find_gaps(self.project_root)
            results["gap_finder"] = [
                g.to_dict() if hasattr(g, "to_dict") else g for g in gap_result.gaps
            ]
        except Exception:
            results["gap_finder"] = []

        return results

    def _run_correctness_subagents(self) -> dict[str, list[Gap]]:
        """Run adversarial correctness analysis.

        Dispatches 3 targeted agents via claude -p:
        - gto-logic: Pure logic errors (off-by-one, wrong operators, inverted conditionals)
        - gto-quality: Maintainability risks and technical debt
        - gto-code-critic: Root cause analysis and causal chains

        Files are written to a temp directory and the agent is instructed to read them.
        This avoids Windows command-line length limits and agent tool-use hangs.

        Returns:
            Dictionary mapping agent name to list of Gap objects
        """
        import subprocess
        import sys
        import tempfile
        from pathlib import Path

        results: dict[str, list[Gap]] = {}

        # Map agent keys to GTO-specific agent names
        agents = [
            ("logic", "gto-logic"),
            ("quality", "gto-quality"),
            ("code-critic", "gto-code-critic"),
        ]

        # Collect Python files for targeted analysis (avoid broad directory scans)
        python_files = self._collect_python_files_for_analysis()

        # Write files to a temp subdirectory WITHIN project_root so claude -p
        # subprocess can access them (Read tool restricted to project dir)
        import uuid
        tmp_subdir = f".claude/gto-temp-{uuid.uuid4().hex[:8]}"
        tmp_path = self.project_root / tmp_subdir

        try:
            tmp_path.mkdir(parents=True, exist_ok=True)

            # Write each file to temp directory preserving structure
            written_files: list[Path] = []
            for pf in python_files:
                try:
                    content = pf.read_text(encoding="utf-8", errors="replace")
                    # Create relative path structure preserving directory hierarchy
                    # e.g. "P:/.claude/skills/gto/lib/session_memoizer.py" -> ".claude/skills/gto/lib/session_memoizer.py"
                    posix = pf.as_posix()  # e.g. "P:/ .claude/skills/gto/lib/session_memoizer.py"
                    rest = posix[3:].replace(":", "")  # strip "P:/" -> ".claude/skills/gto/lib/session_memoizer.py"
                    rel_path = Path(rest)
                    out_file = tmp_path / rel_path
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                    out_file.write_text(content, encoding="utf-8")
                    written_files.append(out_file)
                except OSError as e:
                    logger.warning("Failed to write temp file for %s: %s", pf, e)

            # Build file list from actual written paths (mangled to match on-disk names)
            file_list = "\n".join(f"  - {f.as_posix()}" for f in written_files)

            # Dispatch each agent via claude -p --agent
            for agent_key, agent_name in agents:
                logger.info("Dispatching %s adversarial agent...", agent_name)

                # Build prompt with file paths
                output_path = (tmp_path / "findings.json").as_posix()
                prompt = self._build_correctness_prompt(
                    agent_name, agent_key, tmp_path.as_posix(), file_list, output_path
                )

                try:
                    import shutil

                    # Find claude executable
                    claude_cmd = shutil.which("claude")
                    if not claude_cmd:
                        logger.warning("claude command not found in PATH")
                        results[agent_key] = []
                        continue

                    # Spawn claude -p with the agent
                    # NOTE: Do NOT use --output-format json - it causes hangs with custom agents
                    # when they attempt tool use. Instead, parse JSON from stdout directly.
                    proc = subprocess.Popen(
                        [
                            claude_cmd,
                            "-p",
                            "--agent",
                            agent_name,
                            prompt,
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=str(self.project_root),
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                    )

                    stdout, stderr = proc.communicate(timeout=300)  # 5 minute timeout per agent

                    stdout_text = stdout.decode("utf-8", errors="replace")

                    # Correctness agents return exit code 1 when they find issues,
                    # 0 when no issues found. Exit code 1 is NOT a failure.
                    if proc.returncode not in (0, 1):
                        logger.warning(
                            "Agent %s exited with unexpected code %d: %s",
                            agent_name,
                            proc.returncode,
                            stderr.decode("utf-8", errors="replace")[:200],
                        )
                        results[agent_key] = []
                        continue

                    # Parse JSON from stdout (pipe mode outputs text, not files)
                    gaps = self._parse_json_from_stdout(stdout_text, agent_key)
                    results[agent_key] = gaps
                    logger.info("Loaded %d correctness gaps from %s", len(gaps), agent_name)

                except subprocess.TimeoutExpired:
                    proc.kill()  # type: ignore[possibly-unbound]
                    logger.warning("Agent %s timed out after 300 seconds", agent_name)
                    results[agent_key] = []
                except Exception as e:
                    logger.warning("Failed to dispatch %s agent: %s", agent_name, e)
                    results[agent_key] = []

        finally:
            # Clean up temp directory
            import shutil
            try:
                shutil.rmtree(tmp_path)
            except OSError:
                pass

        return results

    def _collect_python_files_for_analysis(self) -> list[Path]:
        """Collect Python files for targeted adversarial analysis.

        Avoids broad directory scans by limiting to key source files.
        Returns up to 20 files to prevent agent overwhelm.
        """
        from pathlib import Path

        python_files: list[Path] = []
        project_root = Path(self.project_root)

        # Key directories to analyze
        key_dirs = ["lib", "evals"]
        for key_dir in key_dirs:
            dir_path = project_root / key_dir
            if dir_path.exists():
                for pattern in ["*.py"]:
                    python_files.extend(dir_path.glob(pattern))

        # Limit to avoid timeout - take most recently modified
        python_files = sorted(set(python_files), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        return python_files

    def _build_correctness_prompt(
        self,
        agent_name: str,
        agent_key: str,
        base_dir: str,
        file_list: str,
        output_path: str,
    ) -> str:
        """Build targeted prompt for correctness agent.

        Args:
            agent_name: Name of the agent (e.g., 'gto-logic')
            agent_key: Key for this agent ('logic', 'quality', 'code-critic')
            base_dir: Base directory containing the files to analyze
            file_list: Formatted string listing files to analyze

        Returns:
            Formatted prompt string
        """
        # Build focus area description
        if agent_key == "logic":
            focus = "Pure logic errors, off-by-one bugs, wrong operators, inverted conditionals"
        elif agent_key == "quality":
            focus = "Maintainability risks, technical debt, code smells, complex implementations"
        else:  # code-critic
            focus = "Root cause analysis, causal chains, multi-step reasoning failures"

        prompt = f"""Review the following Python files for {agent_name} issues.
Files are located in: {base_dir}
Files to analyze:
{file_list}

Focus areas:
  - {agent_name}: {focus}

IMPORTANT: Read each file using the Read tool, analyze it.

Output your findings as COMPLETE VALID JSON directly to stdout (which will be captured). Write NO prose before or after the JSON — only the JSON object.

JSON format:
{{
  "findings": [
    {{
      "id": "{agent_key.upper()}-001",
      "severity": "HIGH|MEDIUM|LOW",
      "location": "filename.py:line_number",
      "title": "Brief title",
      "description": "Detailed description",
      "evidence": "Specific code snippet"
    }}
  ]
}}

If you find no issues, output: {{"findings": []}}
"""

        return prompt

    def _build_correctness_prompt_with_content(
        self,
        agent_name: str,
        agent_key: str,
        file_contents: dict[str, str],
    ) -> str:
        """Build prompt with file contents embedded for correctness analysis.

        Args:
            agent_name: Name of the agent (e.g., 'gto-logic')
            agent_key: Key for this agent ('logic', 'quality', 'code-critic')
            file_contents: Dictionary mapping file path to file content

        Returns:
            Formatted prompt string with embedded file contents
        """
        # Build focus area description
        if agent_key == "logic":
            focus = "Pure logic errors, off-by-one bugs, wrong operators, inverted conditionals"
        elif agent_key == "quality":
            focus = "Maintainability risks, technical debt, code smells, complex implementations"
        else:  # code-critic
            focus = "Root cause analysis, causal chains, multi-step reasoning failures"

        # Build file content section
        content_lines = ["=== FILE CONTENTS ==="]
        for file_path, content in file_contents.items():
            content_lines.append(f"\n--- {file_path} ---\n{content}")
        content_section = "\n".join(content_lines)

        prompt = f"""Review the following Python code for {agent_name} issues.

{content_section}

Focus areas:
  - {agent_name}: {focus}

Output your findings as JSON with this exact structure:
{{
  "findings": [
    {{
      "id": "{agent_key.upper()}-001",
      "severity": "HIGH|MEDIUM|LOW",
      "location": "filename.py:line_number",
      "title": "Brief title",
      "description": "Detailed description",
      "evidence": "Specific code snippet"
    }}
  ]
}}

If you find no issues, output: {{"findings": []}}
"""

        return prompt

    def _parse_json_from_file(self, file_path: Path, agent_key: str) -> list[Gap]:
        """Parse JSON findings from agent output file."""
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            return self._parse_json_from_stdout(text, agent_key)
        except FileNotFoundError:
            logger.warning("Agent output file not found: %s", file_path)
            return []
        except Exception as e:
            logger.warning("Failed to read agent output file %s: %s", file_path, e)
            return []


    def _parse_json_from_stdout(self, stdout_text: str, agent_key: str) -> list[Gap]:
        """Parse JSON findings from agent stdout text.

        Args:
            stdout_text: Raw stdout text from agent
            agent_key: Key for this agent ('logic', 'quality', 'code-critic')

        Returns:
            List of Gap objects
        """
        import json
        import re

        gaps: list[Gap] = []

        # Try to extract JSON from stdout - look for JSON block or structured output
        json_match = re.search(r"\{[\s\S]*\"findings\"[\s\S]*\}", stdout_text)
        if not json_match:
            # Try simpler pattern - just look for any JSON object with findings
            json_match = re.search(r"\{[\s\S]*\"id\"[\s\S]*\}", stdout_text)

        if not json_match:
            logger.warning("No JSON found in %s stdout", agent_key)
            return gaps

        json_str = json_match.group(0)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # Try to fix common JSON issues from agent output
            # Issue: agents may use single quotes instead of double quotes
            # Fix: convert single-quoted keys/values to double-quoted
            try:
                # Replace single quotes around keys and values
                # This is a simple fix for the common case of single-quoted JSON
                fixed = json_str.replace("'", '"')
                data = json.loads(fixed)
                logger.info("Fixed JSON single-quote issue for %s", agent_key)
            except json.JSONDecodeError:
                # Last attempt: try to extract just the findings array with regex
                findings_match = re.search(r'"findings"\s*:\s*(\[[\s\S]*\])', json_str)
                if findings_match:
                    try:
                        findings_data = json.loads(findings_match.group(0))
                        data = {"findings": findings_data}
                    except json.JSONDecodeError:
                        logger.warning(
                            "Failed to parse JSON from %s stdout after multiple attempts: %s",
                            agent_key,
                            e,
                        )
                        return gaps
                else:
                    logger.warning("Failed to parse JSON from %s stdout: %s", agent_key, e)
                    return gaps

        # Parse using existing method
        return self._parse_adversarial_findings(data, agent_key)

    def _parse_adversarial_findings(self, data: dict[str, Any], agent_name: str) -> list[Gap]:
        """Parse adversarial agent findings into GTO Gap format.

        Args:
            data: JSON data from adversarial agent
            agent_name: Name of the agent (logic, quality, code-critic)

        Returns:
            List of Gap objects
        """
        import re

        gaps: list[Gap] = []

        # Map agent severity to GTO severity
        severity_map = {
            "CRITICAL": "critical",
            "HIGH": "high",
            "MEDIUM": "medium",
            "LOW": "low",
            "blocker": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
        }

        findings = data.get("findings", [])
        for idx, finding in enumerate(findings):
            # Parse location - various formats:
            # - "file.py:123"
            # - "Lines 312-314 vs 360-365"
            # - "Phase 0, T-000 vs T-000.3"
            location = finding.get("location", "")
            file_path: str | None = None
            line_number: int | None = None

            # Try "file:line" format
            if ":" in location:
                parts = location.rsplit(":", 1)
                file_part = parts[0].strip()
                line_part = parts[1].strip() if len(parts) > 1 else ""
                # Check if line_part is a number
                match = re.match(r"(\d+)", line_part)
                if match:
                    file_path = file_part
                    line_number = int(match.group(1))
                elif file_part:
                    file_path = file_part
            # Try "Lines X" format
            elif location:
                match = re.search(r"Lines?\s+(\d+)", location)
                if match:
                    line_number = int(match.group(1))
                # Otherwise use the whole location as file_path if it looks like one
                elif not location.startswith("Phase"):
                    file_path = location

            # Map severity
            raw_severity = finding.get("severity", "medium")
            severity = severity_map.get(raw_severity, raw_severity) or "medium"

            # Build message from title + description
            title = finding.get("title", "Correctness issue detected")
            description = finding.get("description", "")
            if description and len(description) > 200:
                description = description[:197] + "..."
            message = title if not description else f"{title}: {description}"

            # Use provided ID if available
            provided_id = finding.get("id", "")
            gap_id = (
                f"CORR-{provided_id}" if provided_id else f"CORR-{agent_name.upper()}-{idx + 1:03d}"
            )

            gap = Gap(
                gap_id=gap_id,
                type="correctness_gap",
                severity=severity,
                message=message,
                file_path=file_path,
                line_number=line_number,
                source=f"adversarial-{agent_name}",
                confidence=finding.get("confidence", 0.85),
                effort_estimate_minutes=30,
                theme="correctness",
            )
            gaps.append(gap)

        return gaps

    def _run_session_chain_analysis(
        self,
        detector_results: dict[str, Any],
        session_goal_result: Any,
    ) -> ChainAnalysisResult | None:
        """Run session chain analysis to build cross-session narrative.

        Chain analysis runs by default when a transcript is available, regardless of
        query style. It walks the session handoff chain and produces a cross-session
        narrative of what went wrong, what wasn't done, and what should happen next.

        Args:
            detector_results: Results from _run_detectors()
            session_goal_result: Session goal detection result (used as context, not gate)

        Returns:
            ChainAnalysisResult or None if no transcript available
        """
        transcript_path = self.config.transcript_path
        if not transcript_path or not transcript_path.exists():
            return None

        # Extract query focus from question-style detection (informational, not a gate)
        # If no question-style detected, recent_query will be None and the analyzer
        # will produce a general cross-session narrative covering all significant events.
        _, recent_query = self._detect_question_style_from_transcript(transcript_path)

        # Get session chain via robust history_chain.py (survives compaction)
        # Uses parentUuid chain in history.jsonl instead of fragile .jsonl transcript_path links
        chain_result = None
        try:
            from search_research.session_chain import walk_session_chain

            # Resolve session_id from transcript_path for walk_chain_simple
            session_id_for_chain: str | None = None
            try:
                with open(transcript_path, encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if entry.get("sessionId"):
                                session_id_for_chain = entry["sessionId"]
                                break
                        except json.JSONDecodeError:
                            continue
            except (OSError, PermissionError):
                pass

            if not session_id_for_chain:
                logger.debug("Could not resolve session_id from transcript")
                return None

            chain_result = walk_session_chain(
                session_id=session_id_for_chain,
            )
        except Exception as e:
            logger.warning("Failed to traverse session chain: %s", e)
            return None

        # When chain is empty (session not created via /compact), fall back to
        # analyzing the current transcript directly. This ensures GTO produces
        # meaningful output even for fresh sessions without handoff history.
        if not chain_result or not chain_result.entries:
            logger.info("No session chain found, falling back to single-transcript analysis")
            analyzer = SessionChainAnalyzer(self.project_root)
            try:
                single_result = analyzer.analyze(
                    [transcript_path],
                    query=recent_query,
                )
                if single_result.error == "no_transcripts":
                    return None
                return single_result
            except Exception as e:
                logger.warning("Single-transcript fallback analysis failed: %s", e)
                return None

        # Session memoization: check cache before running expensive LLM analysis
        memoizer = SessionMemoizer()
        chain_signature = _build_chain_signature(chain_result.entries) if chain_result.entries else ""

        cached_result, missed_sessions = memoizer.get_cached_chain_result(chain_result.entries)
        if cached_result is not None:
            logger.info(
                "Session chain analysis cache HIT — skipping LLM call for chain %s",
                chain_signature[:40] if chain_signature else "?",
            )
            # Reconstruct ChainAnalysisResult from cached dict
            return ChainAnalysisResult(
                focus=cached_result.get("focus", ""),
                phase=cached_result.get("phase", ""),
                next_steps=cached_result.get("next_steps", []),
                confidence=float(cached_result.get("confidence", 0.0)),
                error=cached_result.get("error"),
                transcripts_processed=cached_result.get("transcripts_processed", 0),
            )

        # Cache miss — run the full analysis with critique loop (max 2 reruns)
        analyzer = SessionChainAnalyzer(self.project_root)
        max_reruns = 2
        analysis: ChainAnalysisResult | None = None

        for attempt in range(max_reruns + 1):
            current_analysis = analyzer.analyze_chain_result(chain_result, query=recent_query)
            if attempt == 0:
                analysis = current_analysis

            grade, feedback = analyzer.critique_grade_chain_result(current_analysis, chain_result)
            if grade == "PASS":
                analysis = current_analysis
                break

            if attempt < max_reruns:
                logger.info(
                    "Critique grade FAIL on attempt %d, rerunning with feedback: %s",
                    attempt + 1,
                    feedback,
                )
                # Rebuild prompt with feedback for rerun
                analysis = self._rerun_chain_analysis(
                    analyzer, chain_result, recent_query, feedback
                )

        # Cache the successful result keyed to the current session
        if analysis is not None and chain_result.entries:
            current_entry = chain_result.entries[-1]
            current_session_id = getattr(current_entry, "session_id", None) or (
                current_entry.get("sessionId") if isinstance(current_entry, dict) else None
            )
            current_transcript_path = (
                getattr(current_entry, "transcript_path", None)
                or (current_entry.get("transcriptPath") if isinstance(current_entry, dict) else None)
            )
            if current_session_id and current_transcript_path:
                try:
                    memoizer.cache_session_result(
                        session_id=current_session_id,
                        transcript_path=(
                            current_transcript_path
                            if isinstance(current_transcript_path, Path)
                            else Path(current_transcript_path)
                        ),
                        chain_depth=chain_result.depth,
                        chain_signature=chain_signature,
                        result={
                            "focus": analysis.focus,
                            "phase": analysis.phase,
                            "next_steps": analysis.next_steps,
                            "confidence": analysis.confidence,
                            "error": analysis.error,
                            "transcripts_processed": analysis.transcripts_processed,
                        },
                    )
                except Exception as e:
                    logger.warning("Session chain analysis cache write failed: %s", e)

        return analysis

    def _detect_question_style_from_transcript(
        self, transcript_path: Path
    ) -> tuple[bool, str | None]:
        """Scan recent transcript messages for question-style intent patterns.

        Args:
            transcript_path: Path to transcript JSONL file

        Returns:
            Tuple of (is_question_style, last_user_message or None)
        """
        # Import here to avoid circular dependency at module load
        try:
            from .lib.session_goal_detector import SessionGoalDetector
        except ImportError:
            from lib.session_goal_detector import SessionGoalDetector

        detector = SessionGoalDetector(self.project_root)

        try:
            with open(transcript_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except (OSError, PermissionError):
            return False, None

        # Scan last 10 user messages for question patterns (newest to oldest)
        user_messages: list[str] = []
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                if entry.get("role") == "user":
                    content = entry.get("content", "")
                    if content:
                        user_messages.append(content)
                        if len(user_messages) >= 10:
                            break
            except json.JSONDecodeError:
                continue

        last_message = user_messages[0] if user_messages else None

        # Check each message for question-style patterns
        for msg in user_messages:
            if detector.is_question_style(msg):
                return True, msg

        return False, last_message

    def _rerun_chain_analysis(
        self,
        analyzer: SessionChainAnalyzer,
        chain_result: Any,
        query: str | None,
        feedback: str | None,
    ) -> ChainAnalysisResult:
        """Rerun chain analysis with critique feedback.

        Args:
            analyzer: SessionChainAnalyzer instance
            chain_result: ChainWalkResult from history_chain.py
            query: Original user query
            feedback: Critique feedback to incorporate

        Returns:
            New ChainAnalysisResult
        """
        try:
            result_json = analyzer._rerun_from_chain_result(chain_result, query, feedback)
            return analyzer._parse_result(result_json, len(chain_result.entries))
        except TimeoutError:
            return ChainAnalysisResult(
                focus="",
                phase="",
                next_steps=[],
                confidence=0.0,
                error="timeout",
                transcripts_processed=len(chain_result.entries),
            )
        except Exception as e:
            logger.warning("Rerun analysis failed: %s", e)
            return ChainAnalysisResult(
                focus="",
                phase="",
                next_steps=[],
                confidence=0.0,
                error="crash",
                transcripts_processed=len(chain_result.entries),
            )

    def format_output(self, result: OrchestratorResult, user_query: str | None = None) -> str:
        """Format orchestrator result as human-readable output.

        Args:
            result: Orchestrator result
            user_query: Optional user query to detect question-style context

        Returns:
            Formatted output string
        """
        if not result.success:
            return f"❌ GTO Analysis Failed: {result.error}"

        if not result.results:
            return "❌ No results available"

        lines: list[str] = []
        lines.append("# GTO Gap Analysis Results")
        lines.append("")
        lines.append(f"**Project:** {result.metadata.get('project_root', 'Unknown')}")
        lines.append(f"**Timestamp:** {result.metadata.get('timestamp', 'Unknown')}")

        # Surface session goal prominently — tell the user what they were working on
        session_goal_meta = result.metadata.get("session_goal")
        if session_goal_meta and session_goal_meta.get("goal"):
            goal = session_goal_meta["goal"]
            conf = session_goal_meta.get("confidence", 0.0)
            lines.append("")
            lines.append(f"**What You Were Working On:** {goal}")
            if conf > 0:
                lines.append(f"_(confidence: {conf:.0%})_")

        # Session Context section — chain analysis for question-style queries (TASK-003)
        chain_meta = result.metadata.get("chain_analysis")
        if chain_meta:
            error = chain_meta.get("error")
            confidence = chain_meta.get("confidence", 0.0)

            lines.append("")
            lines.append("## Session Context")
            lines.append("")

            if error:
                lines.append(f"_(analysis degraded: {error})_")
                lines.append("")

            # Focus / Historical work
            focus = chain_meta.get("focus", "")
            if focus:
                lines.append(f"- **Historical focus:** {focus}")

            # Phase / Status
            phase = chain_meta.get("phase", "")
            if phase:
                lines.append(f"- **Phase/Status:** {phase}")

            # Next steps
            next_steps = chain_meta.get("next_steps", [])
            if next_steps:
                lines.append("- **Next steps:**")
                for step in next_steps:
                    lines.append(f"  - {step}")
            else:
                lines.append("- **Next steps:** _(not yet determined)_")

            # Confidence note
            lines.append(f"_(confidence: {confidence:.0%})_")

        lines.append("")

        # Health report
        if result.health_report:
            health = result.health_report
            score = health.get("overall_score", 0)
            status = health.get("status", "unknown")
            lines.append(f"## Health Score: {score:.0%} ({status.upper()})")
            lines.append("")

            for metric in health.get("metrics", []):
                name = metric.get("name", "unknown")
                score_val = metric.get("score", 0)
                weight = metric.get("weight", 0)
                lines.append(f"- **{name}:** {score_val:.0%} (weight: {weight})")
            lines.append("")

        # Gap summary
        results = result.results
        lines.append("## Gap Summary")
        lines.append("")
        lines.append(f"- **Total Gaps:** {results.total_gap_count}")
        lines.append(f"- **Critical:** {results.critical_count}")
        lines.append(f"- **High:** {results.high_count}")
        lines.append(f"- **Medium:** {results.medium_count}")
        lines.append(f"- **Low:** {results.low_count}")
        lines.append("")

        # Gaps by theme
        lines.append("## Gaps by Theme")
        lines.append("")

        theme_groups: dict[str, list[Gap]] = {}
        for gap in results.gaps:
            theme = gap.theme or "other"
            if theme not in theme_groups:
                theme_groups[theme] = []
            theme_groups[theme].append(gap)

        for theme, gaps in sorted(theme_groups.items()):
            lines.append(f"### {theme.title()}")
            lines.append("")
            for gap in sorted(gaps, key=lambda g: g.severity):
                line = f"- **{gap.severity.upper()}:** {gap.message}"
                if gap.file_path:
                    line += f" ({gap.file_path}"
                    if gap.line_number:
                        line += f":{gap.line_number}"
                    line += ")"
                if gap.recurrence_count > 1:
                    line += f" [seen {gap.recurrence_count}x]"
                lines.append(line)
            lines.append("")

        # Recommended next steps - use RSN formatter for unified output
        # Merge gap findings with skill coverage findings
        gaps_as_dicts = [gap.to_dict() for gap in results.gaps]

        # Synthesize "What to Do Next" — natural language priority recommendation
        # This combines session context + pending CRIT items + top gaps into a direct answer
        what_next = self._synthesize_what_next(result)
        if what_next:
            lines.append("")
            lines.append("## What to Do Next")
            lines.append("")
            lines.append(what_next)
            lines.append("")

        # Get skill coverage findings (suggests relevant skills when gaps=0)
        project_root_str = result.metadata.get("project_root", "")
        project_root_path = Path(project_root_str) if project_root_str else Path.cwd()
        # Derive target_key from project_root to ensure per-project isolation
        # Use relative path from cwd or hash to avoid path length issues
        try:
            target_key = str(project_root_path.relative_to(Path.cwd()))
        except ValueError:
            # If project_root is not relative to cwd, use the absolute path as key
            target_key = str(project_root_path)
        coverage_findings = detect_skill_coverage(
            project_root_path, target_key=target_key, gaps=gaps_as_dicts
        )

        # Combine gap findings and skill coverage findings
        all_findings = gaps_as_dicts + coverage_findings
        if all_findings:
            lines.append("## Recommended Next Steps")
            lines.append("")
            lines.append(format_rsn_from_gaps(all_findings, show_effort=True))

        return "\n".join(lines)

    def format_rsn_quick_output(self, result: OrchestratorResult) -> str:
        """Format only the RSN next-steps section — no verbose headers.

        Args:
            result: Orchestrator result

        Returns:
            Formatted RSN next steps string
        """
        if not result.success:
            return f"❌ GTO Analysis Failed: {result.error}"

        if not result.results:
            return "❌ No results available"

        # Build all_findings exactly as format_output() does
        results = result.results
        gaps_as_dicts = [gap.to_dict() for gap in results.gaps]

        project_root_str = result.metadata.get("project_root", "")
        project_root_path = Path(project_root_str) if project_root_str else Path.cwd()
        try:
            target_key = str(project_root_path.relative_to(Path.cwd()))
        except ValueError:
            target_key = str(project_root_path)
        coverage_findings = detect_skill_coverage(
            project_root_path, target_key=target_key, gaps=gaps_as_dicts
        )

        all_findings = gaps_as_dicts + coverage_findings
        if all_findings:
            return format_rsn_from_gaps(all_findings, show_effort=True)
        return "✅ No gaps found."

    def _synthesize_what_next(self, result: OrchestratorResult) -> str | None:
        """Synthesize a direct "what to do next" recommendation.

        Combines:
        - Session goal (what the user was working on)
        - Chain analysis (what went wrong / what blocked progress)
        - Pending CRIT items from task list (critical blockers already identified)
        - Top gaps by severity

        Returns a natural-language recommendation, not a structured list.

        Args:
            result: Orchestrator result

        Returns:
            Natural language recommendation or None if nothing actionable found
        """
        if not result.success or not result.results:
            return None

        gaps = result.results.gaps
        if not gaps:
            return None

        # Extract session context
        session_goal_meta = result.metadata.get("session_goal")
        chain_meta = result.metadata.get("chain_analysis")

        # Build context string
        context_parts: list[str] = []

        # 1. What was the user working on?
        if session_goal_meta and session_goal_meta.get("goal"):
            context_parts.append(f"You were working on: {session_goal_meta['goal']}")

        # 2. What did chain analysis find?
        if chain_meta:
            phase = chain_meta.get("phase", "")
            focus = chain_meta.get("focus", "")
            next_steps = chain_meta.get("next_steps", [])
            if phase:
                context_parts.append(f"Current phase: {phase}")
            if focus:
                context_parts.append(f"Focus: {focus}")
            if next_steps:
                steps_str = "; ".join(next_steps[:3])
                context_parts.append(f"Next steps from prior sessions: {steps_str}")

        # 3. What CRIT items are pending?
        task_list_gaps = [g for g in gaps if g.source == "TaskListGapDetector"]
        crit_gaps = [
            g
            for g in gaps
            if g.severity in ("critical", "high") and g.source != "TaskListGapDetector"
        ]

        recommendations: list[str] = []

        # Priority 1: Pending CRIT items from task list (explicit user priorities)
        if task_list_gaps:
            items = []
            for g in task_list_gaps[:3]:
                items.append(f"[{g.gap_id}] {g.message}")
            recommendations.append(
                "CRITICAL PRIORITIES (from your task list):\n  - " + "\n  - ".join(items)
            )

        # Priority 2: Critical/high gaps (code problems)
        if crit_gaps:
            top = crit_gaps[0]
            loc = (
                f" ({top.file_path}:{top.line_number})" if top.file_path and top.line_number else ""
            )
            recommendations.append(
                f"MOST PRESSING GAP: {top.message}{loc} [{top.severity.upper()}]"
            )
            if len(crit_gaps) > 1:
                recommendations.append(
                    f"Plus {len(crit_gaps) - 1} more critical/high gaps — see full list below."
                )

        if not recommendations:
            return None

        # Build final synthesis
        lines: list[str] = []
        if context_parts:
            lines.append("**Session Context**")
            for part in context_parts:
                lines.append(f"- {part}")
            lines.append("")

        lines.append("**Recommended Actions**")
        for rec in recommendations:
            lines.append(rec)

        return "\n".join(lines)

    def save_json_artifact(
        self, result: OrchestratorResult, output_path: Path | None = None
    ) -> None:
        """Save results as JSON artifact.

        Args:
            result: Orchestrator result
            output_path: Optional path. Defaults to gto-outputs/gto-artifact-{timestamp}.json
        """
        # Default to gto-outputs/ subdirectory like run_gto_monorepo.py
        if output_path is None:
            output_dir = self.project_root / ".evidence" / "gto-outputs"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"gto-artifact-{timestamp}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        artifact = {
            "gaps": [],
            "total_gap_count": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "timestamp": datetime.now().isoformat(),
            "metadata": result.metadata,
        }

        if result.results:
            artifact["gaps"] = [g.to_dict() for g in result.results.gaps]
            artifact["total_gap_count"] = result.results.total_gap_count
            artifact["critical_count"] = result.results.critical_count
            artifact["high_count"] = result.results.high_count
            artifact["medium_count"] = result.results.medium_count
            artifact["low_count"] = result.results.low_count

        if result.health_report is not None:
            artifact["health_report"] = result.health_report
            # Promote top-level convenience fields
            artifact["overall"] = result.health_report.get("overall_score")
            artifact["dimensions"] = {
                m.get("name", f"metric_{i}"): m["score"]
                for i, m in enumerate(result.health_report.get("metrics", []))
                if isinstance(m, dict) and "name" in m and isinstance(m.get("score"), (int, float))
            }
            # Backward compatibility: old artifacts used 'health' key
            artifact["health"] = artifact["health_report"]
            # Preserve summary fields from old schema
            if result.health_report.get("summary"):
                artifact["summary"] = result.health_report["summary"]
            if result.health_report.get("recommended_next_steps"):
                artifact["recommended_next_steps"] = result.health_report["recommended_next_steps"]

        # Atomic write: write to temp file then rename to prevent corruption on crash
        tmp_path = output_path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w") as f:
                json.dump(artifact, f, indent=2)
            tmp_path.replace(output_path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

        # Automatic cleanup: evict old artifacts after saving new one
        self._evict_old_artifacts(output_path.parent)

    def _evict_old_artifacts(self, output_dir: Path, keep_recent: int = 10) -> None:
        """Evict old artifacts, keeping only the most recent N.

        Prevents unbounded artifact accumulation in gto-outputs/.
        Uses mtime for sorting — most recently modified = most recent.

        Args:
            output_dir: Directory containing artifacts
            keep_recent: Number of recent artifacts to keep (default: 10)
        """
        try:
            artifacts = sorted(
                output_dir.glob("gto-artifact-*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            # Evict all but the most recent keep_recent
            for old_artifact in artifacts[keep_recent:]:
                try:
                    old_artifact.unlink()
                except OSError:
                    # Eviction errors are non-fatal
                    pass
        except OSError:
            # Eviction errors are non-fatal
            pass


def run_gto_analysis(
    project_root: Path | str | None = None,
    terminal_id: str | None = None,
    transcript_path: Path | str | None = None,
    enable_subagents: bool = True,
    enable_health_check: bool = True,
    enable_correctness: bool = True,
    verbose: bool = False,
) -> OrchestratorResult:
    """
    Quick entry point for GTO analysis.

    Args:
        project_root: Project root directory
        terminal_id: Terminal identifier (auto-detected if None)
        transcript_path: Optional transcript path for session goal detection
        enable_subagents: Whether to run AI subagents
        enable_health_check: Whether to run health check
        verbose: Enable verbose output

    Returns:
        OrchestratorResult with analysis results
    """
    config = OrchestratorConfig(
        project_root=Path(project_root) if project_root else None,
        terminal_id=terminal_id or _get_default_terminal_id(),
        transcript_path=Path(transcript_path) if transcript_path else None,
        enable_subagents=enable_subagents,
        enable_health_check=enable_health_check,
        enable_correctness=enable_correctness,
        verbose=verbose,
    )

    orchestrator = GTOOrchestrator(config)
    return orchestrator.run()


if __name__ == "__main__":
    # CLI entry point
    import argparse

    parser = argparse.ArgumentParser(description="GTO v3 Gap Analysis")
    parser.add_argument(
        "--transcript",
        type=Path,
        default=None,
        help="Transcript path for session goal detection",
    )
    parser.add_argument(
        "--subagents",
        action="store_true",
        default=False,
        help="Enable AI subagents (GapFinderSubagent)",
    )
    parser.add_argument(
        "--no-health",
        action="store_true",
        help="Disable health check",
    )
    parser.add_argument(
        "--no-correctness",
        action="store_true",
        help="Disable adversarial correctness analysis (logic, quality, code-critic agents)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON artifact path",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "quick", "both"],
        default="markdown",
        help="Output format",
    )

    args = parser.parse_args()

    # Auto-detect terminal ID using canonical function
    terminal_id = _get_default_terminal_id()

    # project_root removed from CLI args — always use cwd
    project_root = Path.cwd()

    # Run analysis
    result = run_gto_analysis(
        project_root=project_root,
        terminal_id=terminal_id,
        transcript_path=args.transcript,
        enable_subagents=args.subagents,
        enable_health_check=not args.no_health,
        enable_correctness=not args.no_correctness,
        verbose=args.verbose,
    )

    # Output results
    if args.format in ("json", "both"):
        output_path = args.output or None  # Let save_json_artifact use default path
        config = OrchestratorConfig(
            project_root=project_root,
            terminal_id=terminal_id,
            transcript_path=args.transcript,
        )
        # Reuse orchestrator to avoid re-running analysis
        orchestrator = GTOOrchestrator(config)
        orchestrator.save_json_artifact(result, output_path)
        # Use the actual path that was generated
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = (
                config.project_root / ".evidence" / "gto-outputs" / f"gto-artifact-{timestamp}.json"
            )
        print(f"JSON artifact saved to: {output_path}")

    if args.format == "quick":
        config = OrchestratorConfig(
            project_root=project_root,
            terminal_id=terminal_id,
            transcript_path=args.transcript,
        )
        orchestrator = GTOOrchestrator(config)
        quick = orchestrator.format_rsn_quick_output(result)
        print(quick)

    if args.format in ("markdown", "both"):
        config = OrchestratorConfig(
            project_root=project_root,
            terminal_id=terminal_id,
            transcript_path=args.transcript,
        )
        orchestrator = GTOOrchestrator(config)
        markdown = orchestrator.format_output(result)
        print(markdown)

    # Exit code based on success
    sys.exit(0 if result.success else 1)
