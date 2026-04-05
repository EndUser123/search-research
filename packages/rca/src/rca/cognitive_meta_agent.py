#!/usr/bin/env python3
"""
DEPRECATED: Cognitive Meta-Agent Facade
Now delegating to features.uaf (Unified Agent Fabric).
"""
import asyncio
import logging
import sys
from typing import Any

# Ensure UAF is importable

try:
    from uaf import (
        decompose_architecture,
        decompose_debug,
        decompose_rca,
        decompose_verification,
    )
except ImportError:
    # Fallback if UAF not found (safety)
    def decompose_architecture(p):
        return []

    def decompose_rca(p):
        return []

    def decompose_debug(p):
        return []

    def decompose_verification(p):
        return []


logger = logging.getLogger(__name__)


def get_arch_subagents(problem: str) -> str:
    """DEPRECATED: Use features.uaf.decompose_architecture instead."""
    tasks = decompose_architecture(problem)
    return _format_legacy(tasks, "Architecture Analysis")


def get_rca_subagents(problem: str) -> str:
    """DEPRECATED: Use features.uaf.decompose_rca instead."""
    tasks = decompose_rca(problem)
    return _format_legacy(tasks, "Root Cause Analysis")


def get_debug_subagents(problem: str) -> str:
    """DEPRECATED: Use features.uaf.decompose_debug instead."""
    tasks = decompose_debug(problem)
    return _format_legacy(tasks, "Debug Investigation")


def _format_legacy(tasks, mission_name: str) -> str:
    """Format UAF tasks into legacy string format."""
    output = f"\n[SUBAGENT MISSIONS (via UAF) - {mission_name.upper()}]\n"
    output += "=" * 70 + "\n"
    for t in tasks:
        output += f"- {t.name} (Pool: {t.pool})\n  Mission: {t.prompt}\n"
    output += "=" * 70 + "\n"
    return output


async def execute_cognitive_mission(mission_type: str, problem: str) -> dict[str, Any]:
    """DEPRECATED: Use features.uaf.TaskExecutor instead."""
    # This is a minimal wrapper. Full execution logic shifted to UAF.
    from uaf import MissionType, WorkflowDecomposer

    decomposer = WorkflowDecomposer()

    m_type = MissionType.RESEARCH
    if mission_type == "arch":
        m_type = MissionType.ARCHITECTURE
    elif mission_type == "rca":
        m_type = MissionType.RCA
    elif mission_type == "debug":
        m_type = MissionType.DEBUG

    tasks = decomposer.decompose(m_type, problem)
    return {
        "mission": mission_type,
        "tasks_decomposed": len(tasks),
        "note": "Execution via legacy facade is discouraged. Use UAF TaskExecutor.",
        "tasks": [{"id": t.id, "prompt": t.prompt} for t in tasks],
    }


if __name__ == "__main__":
    import json

    if len(sys.argv) < 3:
        print("DEPRECATED: Delegates to UAF.")
        print("Usage: python cognitive_meta_agent.py <arch|rca|debug> '<problem>'")
        sys.exit(1)

    cmd = sys.argv[1]
    prob = sys.argv[2]

    if cmd in ["arch", "rca", "debug"]:
        result = asyncio.run(execute_cognitive_mission(cmd, prob))
        print(json.dumps(result, indent=2))
    else:
        print(f"Unknown command: {cmd}")
