"""
Test suite for skill-first enforcement system.

This module provides comprehensive test coverage for the three-layer enforcement pipeline:
- Layer 1: UserPromptSubmit → skill_enforcer.py writes intent files
- Layer 2: PreToolUse → Skill-first gate with TTL and TOCTOU retry
- Layer 3: Stop → Execution gate verifies Skill() was called

Coverage includes:
- Intent file lifecycle (creation, schema validation, deletion)
- TTL enforcement (90s expiration, env var override, ISO fallback)
- TOCTOU retry loop (exponential backoff, error paths)
- Help flag detection (universal --help/--list patterns)
- Prose bypass detection (Stop hook logic)
- Pattern 2 exemption (loaded_skill bypass)
- Multi-terminal isolation (concurrent operations)
- Three-tier path lookup (primary/secondary/fallback)
- Regression tests (ARCH-001 through ARCH-007)
"""

__version__ = "1.0.0"
