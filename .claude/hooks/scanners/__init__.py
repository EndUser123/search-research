#!/usr/bin/env python3
"""
Hook Scanners Module
====================

Fast validation scanners for Stop hook enhancement.

Based on patterns from:
- LLM Guard (protectai/llm-guard)
- FACTSCORE (linzeyu/FACTSCORE)
- Reflexion (noahshinn024/reflexion)
- Voyager (MinecraftYuan/Voyager)
"""

from .agreement_consistency_scanner import AgreementConsistencyScanner
from .base_scanner import BaseScanner, ScanResult, ScanStatus
from .hallucination_scanner import HallucinationScanner
from .intent_drift_scanner import IntentDriftScanner
from .pii_scanner import PIIScanner
from .reflexion_validator import ReflexionValidator

__all__ = [
    "BaseScanner",
    "ScanResult",
    "ScanStatus",
    "PIIScanner",
    "ReflexionValidator",
    "HallucinationScanner",
    "IntentDriftScanner",
    "AgreementConsistencyScanner",
]
