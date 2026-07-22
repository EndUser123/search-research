#!/usr/bin/env python3
'''validate_check - certify a run manifest and evidence per-phase dispositions.

Module-level public entry: validate_run(run_id).
'''
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

ARTIFACTS_ROOT = Path(os.environ.get("ARTIFACTS_ROOT", "P:/.claude/.artifacts"))
CACHE_DIR = ARTIFACTS_ROOT / Path("check-cache")

VALIDATOR_SCHEMA_VERSION = "check.validator.v1"
EVIDENCE_SCHEMA_VERSION = "check.evidence.v1"
MANIFEST_SCHEMA_VERSION = "check.manifest.v1"

PHASE_STATES = frozenset(["PENDING", "PASS", "FAIL", "SKIP"])
TERMINAL_VERDICTS = frozenset(["CLEAN", "FINDINGS", "ERROR", "BLOCKED", "INCOMPLETE"])
REQUIRED_PHASES = ["baseline", "behavioral", "property", "subprocess", "mutation", "review"]


@dataclass
class ValidatorResult:
    run_id: str
    schema_version: str
    manifest_loaded: bool
    manifest_hash: str
    evidence_loaded: bool
    evidence_schema_valid: bool
    evidence_schema_version: str
    phase_states: Dict[str, str]
    terminal_verdict: str
    eligible_to_promote: bool
    failure_phase: Optional[str]
    reason_code: Optional[str]
    message: str
    validated_at: str


def _git_hash(ref):
    try:
        out = subprocess.run(["git", "rev-parse", "--short", ref], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""

