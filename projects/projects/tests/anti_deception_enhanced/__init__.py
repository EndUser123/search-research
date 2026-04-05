"""
Comprehensive Test Suite for Enhanced Anti-Deception Architecture
=================================================================

This test suite validates all integrated functionality of the Enhanced Anti-Deception
Architecture implemented across Claude Code hooks.

Test Categories:
- Unit Tests: Individual component validation
- Integration Tests: Cross-component communication
- Performance Tests: Sub-2 second validation overhead
- Scenario Tests: Real-world workflow validation

Architecture Components Tested:
1. PostToolUse BalancedValidationLogic
2. LLM Supervisor with hybrid validation
3. PreToolUse TDD enforcement
4. Cross-hook communication system
5. Configuration management
6. Evidence collection and storage

Performance Requirements:
- Validation overhead: < 2 seconds
- Memory usage: < 100MB additional
- Async execution: < 0.5s parallel processing
- Cache hit rate: > 85%
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add paths for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "hooks")
)
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "__csf", "lib")
)

# Test configuration
ENHANCED_TEST_CONFIG = {
    "validation_logic": {
        "critical_blocks": ["security_violations", "data_corruption", "system_damage"],
        "errors_with_feedback": [
            "missing_evidence",
            "incomplete_validation",
            "test_failures",
        ],
        "warnings_allow": ["performance_degradation", "style_issues", "minor_risks"],
    },
    "performance_requirements": {
        "max_validation_overhead": 2.0,  # seconds
        "max_memory_overhead": 100,  # MB
        "min_cache_hit_rate": 0.85,  # 85%
        "max_parallel_processing": 0.5,  # seconds
    },
    "test_scenarios": {
        "code_edit": {"tools": ["Edit"], "risk_level": "medium"},
        "file_write": {"tools": ["Write"], "risk_level": "high"},
        "bash_command": {"tools": ["Bash"], "risk_level": "critical"},
        "web_search": {"tools": ["WebSearch"], "risk_level": "low"},
    },
}


@pytest.fixture
def temp_test_file():
    """Create a temporary test file for testing."""
    temp_dir = Path("P:\\tests\\anti_deception_enhanced\\temp")
    temp_dir.mkdir(exist_ok=True)
    test_file = temp_dir / "test_file.txt"
    test_file.write_text("Test content")
    yield str(test_file)
    # Cleanup
    if test_file.exists():
        test_file.unlink()


@pytest.fixture
def mock_hook_context():
    """Mock hook context for testing."""
    return {
        "tool_name": "Edit",
        "tool_result": {"success": True},
        "duration_ms": 150,
        "metadata": {"file_path": "test.py"},
    }


@pytest.fixture
def sample_validation_result():
    """Sample validation result for testing."""
    return {
        "is_valid": True,
        "confidence": 0.95,
        "validation_type": "balanced",
        "critical_issues": [],
        "errors": [],
        "warnings": ["minor_performance_impact"],
        "execution_time": 0.8,
        "cache_hit": True,
    }
