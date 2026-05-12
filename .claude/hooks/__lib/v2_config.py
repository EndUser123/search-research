# V2 Configuration — feature flags for semantic state architecture.
from __future__ import annotations

import os

# Master switch — disables all V2 layers when False
V2_ENABLED = os.environ.get("V2_ENABLED", "true").lower() == "true"

# Shadow mode: V2 logs decisions but V1 enforces (default: True)
V2_SHADOW_MODE = os.environ.get("V2_SHADOW_MODE", "true").lower() == "true"

# Individual layer toggles
V2_SEMANTIC_MATCHER_ENABLED = os.environ.get("V2_SEMANTIC_MATCHER_ENABLED", "true").lower() == "true"
V2_PHASE_MACHINE_ENABLED = os.environ.get("V2_PHASE_MACHINE_ENABLED", "true").lower() == "true"
V2_EVIDENCE_COLLECTOR_ENABLED = os.environ.get("V2_EVIDENCE_COLLECTOR_ENABLED", "true").lower() == "true"

# Authority levels (used when V2_SHADOW_MODE = False)
# "off"           → V1 only, V2 disabled
# "supersede_only"→ V2 handles auto-supersede, V1 handles enforcement
# "applicability" → V2 handles phase-aware applicability + supersede, V1 handles output checks
# "full"          → V2 owns all decisions
V2_AUTHORITY = os.environ.get("V2_AUTHORITY", "off")

# Phase inference weights
EVIDENCE_WEIGHT = float(os.environ.get("V2_EVIDENCE_WEIGHT", "1.0"))
TURN_MODE_WEIGHT = float(os.environ.get("V2_TURN_MODE_WEIGHT", "0.7"))
CONTENT_MARKER_WEIGHT = float(os.environ.get("V2_CONTENT_WEIGHT", "0.5"))

# Evidence thresholds
MIN_FILES_FOR_IMPLEMENTATION_PHASE = int(os.environ.get("V2_MIN_FILES", "1"))
MIN_TESTS_FOR_VERIFICATION_PHASE = int(os.environ.get("V2_MIN_TESTS", "1"))
