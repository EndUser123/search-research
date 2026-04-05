#!/usr/bin/env python3
"""
hook_constants.py
==================

Shared constants for CSF NIP hooks.

This module provides centralized, single-source definitions for constants
used across multiple hooks. This prevents drift and maintenance issues when
the same constant is defined in multiple places.

AUTHOR: CSF NIP
VERSION: 1.0
"""

from __future__ import annotations

# Skills that are KNOWLEDGE/REFERENCE type (don't require execution)
# These skills provide consultation, documentation, or reference material
# without requiring specific tool execution patterns.
KNOWLEDGE_SKILLS = frozenset({
    "standards",
    "constraints",
    "techniques",
    "evidence-tiers",
    "constitutional-patterns",
    "cognitive-frameworks",
    "prompt_refiner",
    "library-first",
    "solo-dev-authority",
    "data-safety-vcs",
    "chs",  # Cognitive Steering Framework
    "cks",  # Constitutional Knowledge System
    "analyze",  # Analysis and documentation
    "discover",  # Codebase discovery
    "ask",  # Consultation
    "reflect",  # Post-mortem reflection
    "s",  # Strategy skill (knowledge/consultation)
})

# Note: pre-mortem is NOT in KNOWLEDGE_SKILLS because it declares workflow_steps
# in its SKILL.md frontmatter. The Stop hook enforces pre-mortem as an execution
# target, and PreToolUse_workflow_steps_gate.py enforces Skill-first gating.
