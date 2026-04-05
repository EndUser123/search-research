"""Test fixtures for PRD Verifier testing.

This module provides reusable fixtures for testing the PRD verifier skill
with various scenarios including passing, failing, and partial verification cases.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml


# ============================================================================
# TINY REPOSITORY FIXTURES
# ============================================================================


@pytest.fixture
def tiny_repo_complete(tmp_path: Path) -> dict[str, Any]:
    """Create a tiny repository with complete PRD, plan, and implementation.

    This fixture represents a PASSING verification scenario where:
    - All PRD requirements are addressed in the plan
    - All tasks are completed
    - Implementation matches specifications
    - No user concerns exist

    Expected: Verification PASS
    """
    repo = {
        "root": tmp_path,
        "prd": tmp_path / "prd.md",
        "plan": tmp_path / "plan.md",
        "code": tmp_path / "src",
        "tests": tmp_path / "tests",
    }

    # Create PRD with complete technical specifications
    repo["prd"].write_text("""# Product Requirements Document: User Authentication

## Technical Specifications

The system shall implement secure user authentication with:
- Password hashing using bcrypt (cost factor 12)
- JWT token-based sessions with 256-bit secrets
- Session expiration after 24 hours
- Secure password validation (min 8 chars, 1 uppercase, 1 number)

## API Contract

### POST /api/auth/login
- Request: `{username: string, password: string}`
- Response: `{token: string, expires_at: ISO8601, user_id: UUID}`

### POST /api/auth/logout
- Request: `{token: string}`
- Response: `{success: boolean}`

## Data Model

Users table:
- id: UUID primary key
- username: unique string, max 50 chars
- password_hash: bcrypt hash
- email: unique string, validated format
- created_at: timestamp with timezone
- last_login: timestamp nullable

## Security Requirements

- All passwords must be hashed before storage
- JWT tokens must be signed with HS256 algorithm
- Rate limiting: 5 login attempts per IP per hour
- Account lockout after 10 failed attempts
""")

    # Create plan with all tasks completed
    repo["plan"].write_text("""# Feature: User Authentication

## Acceptance Criteria
- [x] TASK-001: Implement bcrypt password hashing (cost 12)
- [x] TASK-002: Create JWT token generation (HS256, 256-bit secret)
- [x] TASK-003: Build POST /api/auth/login endpoint
- [x] TASK-004: Build POST /api/auth/logout endpoint
- [x] TASK-005: Add password validation (8+ chars, 1 upper, 1 number)
- [x] TASK-006: Implement session expiration (24 hours)
- [x] TASK-007: Add rate limiting (5 attempts/hour)
- [x] TASK-008: Implement account lockout (10 failed attempts)

## Success Metrics
- [x] TASK-009: All unit tests passing (100% coverage)
- [x] TASK-010: Integration tests passing
- [x] TASK-011: Security audit completed

## RALPH_STATUS
- EXIT_SIGNAL: true
- completion_indicators: 11
""")

    # Create implementation code
    repo["code"].mkdir()
    (repo["code"] / "auth.py").write_text("""import bcrypt
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional

def hash_password(password: str) -> str:
    '''Hash password using bcrypt with cost factor 12.'''
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed: str) -> bool:
    '''Verify password against hash.'''
    return bcrypt.checkpw(password.encode(), hashed.encode())

def generate_token(user_id: str) -> tuple[str, datetime]:
    '''Generate JWT token valid for 24 hours.'''
    secret = secrets.token_urlsafe(32)  # 256-bit secret
    expires = datetime.now() + timedelta(hours=24)
    payload = {'user_id': user_id, 'exp': expires}
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token, expires

def validate_password_strength(password: str) -> bool:
    '''Validate password meets requirements.'''
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    return True
""")

    (repo["code"] / "api.py").write_text("""from flask import Flask, request, jsonify
from .auth import hash_password, verify_password, generate_token

app = Flask(__name__)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    # Implementation complete
    return jsonify({'token': token, 'expires_at': expires, 'user_id': user_id})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    # Implementation complete
    return jsonify({'success': True})
""")

    # Create tests
    repo["tests"].mkdir()
    (repo["tests"] / "test_auth.py").write_text("""import pytest
from src.auth import hash_password, verify_password, generate_token, validate_password_strength

def test_password_hashing():
    password = "Test1234"
    hashed = hash_password(password)
    assert verify_password(password, hashed)

def test_password_validation():
    assert validate_password_strength("Test1234") == True
    assert validate_password_strength("weak") == False

def test_token_generation():
    token, expires = generate_token("user123")
    assert token
    assert expires > datetime.now()
""")

    return repo


@pytest.fixture
def tiny_repo_incomplete(tmp_path: Path) -> dict[str, Any]:
    """Create a tiny repository with incomplete implementation.

    This fixture represents a FAILING verification scenario where:
    - Some PRD requirements are not addressed
    - Some tasks are incomplete
    - Implementation gaps exist
    - User concerns are present

    Expected: Verification FAIL
    """
    repo = {
        "root": tmp_path,
        "prd": tmp_path / "prd.md",
        "plan": tmp_path / "plan.md",
        "code": tmp_path / "src",
        "tests": tmp_path / "tests",
    }

    # Create PRD with comprehensive requirements
    repo["prd"].write_text("""# Product Requirements Document: User Authentication

## Technical Specifications
- Password hashing using bcrypt
- JWT token-based sessions
- Session expiration after 24 hours
- OAuth 2.0 integration for third-party login
- Multi-factor authentication (TOTP)
- Biometric authentication support

## API Contract
### POST /api/auth/login
- Request: `{username, password}`
- Response: `{token, expires_at}`

### POST /api/auth/oauth/callback
- Request: `{provider, code}`
- Response: `{token, user_info}`

## Security Requirements
- Rate limiting: 5 attempts per hour
- Account lockout: 10 failed attempts
- IP-based blocking after lockout
- Email verification required
""")

    # Create plan with incomplete tasks
    repo["plan"].write_text("""# Feature: User Authentication

## Acceptance Criteria
- [x] TASK-001: Implement bcrypt password hashing
- [ ] TASK-002: Create JWT token generation
- [ ] TASK-003: Build login endpoint
- [ ] TASK-004: Add rate limiting
- [ ] TASK-005: Implement account lockout
- [ ] TASK-006: Add OAuth 2.0 integration
- [ ] TASK-007: Add multi-factor authentication
- [ ] TASK-008: Add biometric support

## Success Metrics
- [x] TASK-009: Password hashing working
- [ ] TASK-010: All tests passing

## RALPH_STATUS
- EXIT_SIGNAL: false
- completion_indicators: 2
""")

    # Create incomplete implementation
    repo["code"].mkdir()
    (repo["code"] / "auth.py").write_text("""import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()

# Missing: verify_password, generate_token, OAuth, MFA, biometrics
""")

    repo["tests"].mkdir()
    (
        repo["tests"] / "test_auth.py"
    ).write_text("""# Incomplete tests - only hashing tested

def test_password_hashing():
    from src.auth import hash_password
    hashed = hash_password("test")
    assert hashed
""")

    return repo


@pytest.fixture
def tiny_repo_no_prd(tmp_path: Path) -> dict[str, Any]:
    """Create a tiny repository without a PRD file.

    This fixture represents a scenario where:
    - No PRD document exists
    - Plan and implementation are present
    - Verification should handle gracefully (assume passing)

    Expected: Verification PASS (graceful handling)
    """
    repo = {
        "root": tmp_path,
        "prd": None,  # No PRD
        "plan": tmp_path / "plan.md",
        "code": tmp_path / "src",
    }

    repo["plan"].write_text("""# Feature: Simple Task

## Acceptance Criteria
- [x] TASK-001: Implement basic functionality

## RALPH_STATUS
- EXIT_SIGNAL: true
- completion_indicators: 1
""")

    repo["code"].mkdir()
    (repo["code"] / "main.py").write_text("""def main():
    print("Hello, World!")
""")

    return repo


# ============================================================================
# CHAT TRANSCRIPT FIXTURES
# ============================================================================


@pytest.fixture
def transcript_with_concerns(tmp_path: Path) -> Path:
    """Create a chat transcript with user concerns.

    This transcript contains user concerns that should be detected
    during verification and cause critical issues.
    """
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text("""{"role": "assistant", "content": "I'll implement the login endpoint"}
{"role": "user", "content": "This approach is wrong, we need OAuth 2.0 instead"}
{"role": "assistant", "content": "I'll add unit tests for the auth module"}
{"role": "user", "content": "The tests don't cover edge cases like SQL injection"}
{"role": "assistant", "content": "I'll add rate limiting"}
{"role": "user", "content": "Rate limiting should be per-user, not per-IP"}
{"role": "assistant", "content": "Implementation complete"}
{"role": "user", "content": "Blocker: Missing email verification requirement"}
""")
    return transcript


@pytest.fixture
def transcript_clean(tmp_path: Path) -> Path:
    """Create a clean chat transcript without concerns.

    This transcript represents a smooth development process
    without user concerns or blockers.
    """
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text("""{"role": "assistant", "content": "I'll implement the login endpoint"}
{"role": "user", "content": "Sounds good, proceed"}
{"role": "assistant", "content": "Adding unit tests now"}
{"role": "user", "content": "Great, thanks"}
""")
    return transcript


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================


@pytest.fixture
def verification_config_enabled(tmp_path: Path) -> Path:
    """Create a config file with verification enabled."""
    config = tmp_path / "config.yaml"
    config_data = {
        "version": 1,
        "verification": {
            "enabled": True,
            "skill": "prd-verifier",
            "write_report": ".claude/loop/verification-report.md",
            "fields": ["prd_coverage", "spec_compliance", "implementation_quality"],
        },
        "exit_policy": {
            "min_completion_indicators": 2,
            "require_exit_signal": True,
            "require_all_tasks_complete": True,
            "require_verification_pass": True,
        },
    }
    config.write_text(yaml.dump(config_data))
    return config


@pytest.fixture
def verification_config_disabled(tmp_path: Path) -> Path:
    """Create a config file with verification disabled."""
    config = tmp_path / "config.yaml"
    config_data = {
        "version": 1,
        "verification": {
            "enabled": False,
        },
    }
    config.write_text(yaml.dump(config_data))
    return config


@pytest.fixture
def verification_config_custom_thresholds(tmp_path: Path) -> Path:
    """Create a config file with custom verification thresholds."""
    config = tmp_path / "config.yaml"
    config_data = {
        "version": 1,
        "verification": {
            "enabled": True,
            "skill": "prd-verifier",
            "write_report": ".claude/loop/verification-report.md",
            "fields": ["prd_coverage", "spec_compliance", "implementation_quality"],
            "thresholds": {
                "prd_coverage_min": 90.0,
                "spec_compliance_min": 85.0,
                "quality_score_min": 8,
            },
        },
    }
    config.write_text(yaml.dump(config_data))
    return config


# ============================================================================
# LOOP STATE FIXTURES
# ============================================================================


@pytest.fixture
def loop_state_complete(tmp_path: Path) -> dict[str, Any]:
    """Create a complete loop state for testing."""
    return {
        "current_task_id": "TASK-011",
        "completed_tasks": ["TASK-001", "TASK-002", "TASK-003"],
        "failed_tasks": [],
        "completion_indicators": 11,
        "ralph_status": {
            "EXIT_SIGNAL": True,
        },
        "metadata": {
            "plan_path": str(tmp_path / "plan.md"),
            "transcript_path": str(tmp_path / "transcript.jsonl"),
        },
    }


@pytest.fixture
def loop_state_incomplete(tmp_path: Path) -> dict[str, Any]:
    """Create an incomplete loop state for testing."""
    return {
        "current_task_id": "TASK-003",
        "completed_tasks": ["TASK-001"],
        "failed_tasks": [],
        "completion_indicators": 2,
        "ralph_status": {
            "EXIT_SIGNAL": False,
        },
        "metadata": {
            "plan_path": str(tmp_path / "plan.md"),
            "transcript_path": str(tmp_path / "transcript.jsonl"),
        },
    }


# ============================================================================
# VERIFICATION REPORT EXAMPLES
# ============================================================================


@pytest.fixture
def example_report_pass() -> str:
    """Example of a passing verification report."""
    return """# Verification Report

**Generated:** 2026-03-15T12:00:00
**Status:** ✓ PASS

## Summary
**Verification PASS**

- PRD Coverage: 100.0% (11/11 requirements)
- Spec Compliance: 100.0% (8/8 requirements)
- Implementation Quality: 10/10 (0 critical issues)

## PRD Coverage
- Requirements addressed: 11/11
- Coverage percentage: 100.0%

### All Requirements Met

### Details
- Password hashing using bcrypt: ✓
- JWT token-based sessions: ✓
- Session expiration after 24 hours: ✓
- POST /api/auth/login endpoint: ✓
- POST /api/auth/logout endpoint: ✓
- Password validation (8+ chars, 1 upper, 1 number): ✓
- Rate limiting (5 attempts/hour): ✓
- Account lockout (10 failed attempts): ✓
- Unit tests passing: ✓
- Integration tests passing: ✓
- Security audit completed: ✓

## Spec Compliance
- Spec requirements met: 8/8
- Compliance percentage: 100.0%

### Details
Found 8 spec sections in PRD

## Implementation Quality
- Code quality score: 10/10

### Details
- Task completion rate: 100.0%
- No user concerns detected
"""


@pytest.fixture
def example_report_fail() -> str:
    """Example of a failing verification report."""
    return """# Verification Report

**Generated:** 2026-03-15T12:00:00
**Status:** ✗ FAIL

## Summary
**Verification FAIL**

- PRD Coverage: 25.0% (2/8 requirements)
- Spec Compliance: 40.0% (2/5 requirements)
- Implementation Quality: 3/10 (3 critical issues)

## PRD Coverage
- Requirements addressed: 2/8
- Coverage percentage: 25.0%

### Missing Requirements
- JWT token-based sessions
- Session expiration after 24 hours
- OAuth 2.0 integration
- Multi-factor authentication
- Biometric authentication support
- IP-based blocking after lockout

### Details
- Password hashing using bcrypt: ✓
- Rate limiting: ✓
- JWT token-based sessions: ✗
- Session expiration after 24 hours: ✗
- OAuth 2.0 integration: ✗
- Multi-factor authentication: ✗
- Biometric authentication support: ✗
- IP-based blocking: ✗

## Spec Compliance
- Spec requirements met: 2/5
- Compliance percentage: 40.0%

### Deviations
- Missing OAuth 2.0 callback endpoint
- No TOTP implementation
- No biometric support

### Details
Found 5 spec sections in PRD

## Implementation Quality
- Code quality score: 3/10

### Critical Issues
- User concern: This approach is wrong, we need OAuth 2.0 instead
- User concern: The tests don't cover edge cases like SQL injection
- User concern: Blocker: Missing email verification requirement

### Recommendations
- Address user concerns before completion
- Complete all remaining tasks
- Add OAuth 2.0 integration
- Implement multi-factor authentication
- Add comprehensive edge case testing

### Details
- Task completion rate: 25.0%
- Found 3 user concerns
"""


@pytest.fixture
def example_report_partial() -> str:
    """Example of a partial/partially passing verification report."""
    return """# Verification Report

**Generated:** 2026-03-15T12:00:00
**Status:** ✗ FAIL

## Summary
**Verification FAIL**

- PRD Coverage: 75.0% (6/8 requirements)
- Spec Compliance: 100.0% (5/5 requirements)
- Implementation Quality: 6/10 (1 critical issue)

## PRD Coverage
- Requirements addressed: 6/8
- Coverage percentage: 75.0%

### Missing Requirements
- Multi-factor authentication
- Biometric authentication support

### Details
- Password hashing using bcrypt: ✓
- JWT token-based sessions: ✓
- Session expiration after 24 hours: ✓
- POST /api/auth/login endpoint: ✓
- POST /api/auth/logout endpoint: ✓
- Rate limiting: ✓
- Multi-factor authentication: ✗
- Biometric authentication support: ✗

## Spec Compliance
- Spec requirements met: 5/5
- Compliance percentage: 100.0%

### Details
Found 5 spec sections in PRD

## Implementation Quality
- Code quality score: 6/10

### Critical Issues
- User concern: Missing email verification requirement

### Recommendations
- Address user concerns before completion
- Complete remaining MFA and biometric tasks

### Details
- Task completion rate: 75.0%
- Found 1 user concern
"""
