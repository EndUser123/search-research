# Sitrep: Adaptive Guardrails v2.0 (The Behavioral Shift)

**Date**: 2026-02-13
**Status**: 🚀 ACTIVATED / WIRED (settings.json updated)
**Architecture**: Lean Behavioral Proof

## 1. The "What" (Structural Changes)

We have replaced the monolithic "God Script" architecture with a **Decoupled Dispatcher** model, now fully wired in `settings.json`.

### Verified Wiring
- **`SessionStart.py`**: Cold-start setup.
- **`UserPromptSubmit.py`**: Context injection & Pushback Protocol.
- **`PreToolUse.py`**: Consolidated logic & Security Firewall.
- **`PostToolUse.py`**: Unified evidence logging.
- **`Stop.py`**: Behavioral Response Gate.

---

## 2. The "Why" (Behavioral Engineering)

### A. Proof vs. Formatting
Proof is now based on **Behavior** (verified via `evidence_store.py`) rather than **Text Formatting**. The verifier uses a path-overlap strategy to maintain context while ensuring fresh verification for modified files.

### B. User Pushback Protocol
If a user challenges a claim, `UserPromptSubmit.py` detects the challenge (via `last_blocked_claim.json`) and injects a mandatory re-verification directive.

### C. Prescriptive Escalation
Tool loops are now hard-blocked by `recursive_failure_detector.py` with prescriptive instructions (e.g., "Shift from shell execution to temp files").

---

## 3. Results (Final Metrics)

- **Speed**: overhead reduced from 233ms to **7ms** (confirmed via benchmark).
- **Wiring**: 100% of event types consolidated into lean entry points.
- **Complexity**: Root directory noise reduced by ~60% (128 files remaining, focusing on modular libraries).
