# Extraction Refactoring Pattern

## Purpose

Reduce cyclomatic complexity by extracting focused helper methods based on single responsibility principle.

## When to Apply

- **CC > 15**: Function is too complex
- **Sequential logic**: Multiple steps can be separated
- **Repeated patterns**: Same logic used multiple times
- **Testability**: Hard to test complex function

## Pattern

### Before (CC 18)
```python
def _validate_skill_claim(self, claim_text: str, context: dict) -> ScanResult:
    """Validate skill existence claim against tool evidence."""
    # Extract skill name
    skill_match = re.search(r"/([\w-]+)", claim_text)
    if not skill_match:
        return ScanResult(ScanStatus.PASS, self.name, reason="No skill name in claim")
    skill_name = skill_match.group(1)

    # Check tool results
    tool_results = context.get("toolResults", []) if isinstance(context.get("toolResults"), list) else []
    has_evidence = False
    evidence_type = None

    for result in tool_results:
        if not isinstance(result, dict):
            continue

        if result.get("name") == "Bash" or "command" in result:
            command = result.get("command", result.get("cmd", ""))
            if "skills/" in command.lower() or skill_name in command:
                has_evidence = True
                evidence_type = "Bash"
                break
        # ... more evidence checking ...

    if not has_evidence:
        suggestion = self._find_similar_skill(skill_name)
        # ... build result ...

    return ScanResult(...)
```

### After (CC 2)
```python
def _validate_skill_claim(self, claim_text: str, context: dict) -> ScanResult:
    """Validate skill existence claim against tool evidence."""
    skill_name = self._extract_skill_name(claim_text)
    if not skill_name:
        return ScanResult(ScanStatus.PASS, self.name, reason="No skill name in claim")

    evidence = self._check_tool_evidence(context, skill_name)
    return self._build_skill_claim_result(evidence, skill_name, claim_text, context)

def _extract_skill_name(self, claim_text: str) -> str | None:
    """Extract skill name from claim text."""
    skill_match = re.search(r"/([\w-]+)", claim_text)
    return skill_match.group(1) if skill_match else None

def _check_tool_evidence(self, context: dict, skill_name: str) -> dict:
    """Check tool results for evidence about skill existence."""
    tool_results = (
        context.get("toolResults", [])
        if isinstance(context.get("toolResults"), list)
        else []
    )

    for result in tool_results:
        if not isinstance(result, dict):
            continue

        if result.get("name") == "Bash" or "command" in result:
            command = result.get("command", result.get("cmd", ""))
            if "skills/" in command.lower() or skill_name in command:
                return {"has_evidence": True, "evidence_type": "Bash"}

        # ... other evidence types ...

    return {"has_evidence": False, "evidence_type": None}

def _build_skill_claim_result(self, evidence: dict, skill_name: str, claim_text: str, context: dict) -> ScanResult:
    """Build ScanResult based on evidence check."""
    if not evidence["has_evidence"]:
        suggestion = self._find_similar_skill(skill_name)
        suggestion_text = f" Did you mean /{suggestion}?" if suggestion else ""

        # Log blocked claim if logging is enabled
        if _LOG_ENABLED:
            evidence_count = len([r for r in context.get("toolResults", []) if isinstance(r, dict)])
            similar_skill = suggestion if suggestion else "None"
            _logger.info(f"{claim_text} | Evidence: {evidence_count} | Similar: /{similar_skill}")

        return ScanResult(
            ScanStatus.FAIL,
            self.name,
            matched_text=claim_text,
            reason=(
                f"Unverified skill existence claim: \"{claim_text}\". "
                f"Provide tool evidence (Bash ls skills/, Grep, or Read SKILL.md) "
                f"before claiming skill doesn't exist.{suggestion_text}"
            ),
            severity="HIGH",
            suggestion=f"Run: ls P:/.claude/skills/ | grep {skill_name}",
        )

    return ScanResult(
        ScanStatus.PASS,
        self.name,
        reason=f"Skill claim verified with {evidence['evidence_type']} evidence",
    )
```

## Results

- **Complexity**: CC 18 → CC 2 (89% reduction)
- **Test Regressions**: 0 (all 24 tests passing)
- **Performance**: +8.3% improvement (0.12ms → 0.11ms)
- **Maintainability**: Each helper has single responsibility
- **Testability**: Can test each helper independently

## Key Principles

1. **Extract by responsibility**: Each helper does ONE thing
2. **Sequential steps**: Extract step 1 → step 2 → step 3
3. **Clear naming**: `_extract_X`, `_check_X`, `_build_X` pattern
4. **Minimal changes**: No behavior changes, only extraction

## Related

- CKS Entry: `pat_251173f3a7324bd0` - Extraction Refactoring for CC Reduction
- Single Responsibility Principle (SRP)
- Don't Repeat Yourself (DRY)
