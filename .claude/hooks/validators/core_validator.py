"""
Core Validator Engine v2
Config-driven validation with multi-error aggregation and severity tiers.
"""
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import yaml
except ImportError:
    # Fallback for environments without PyYAML
    yaml = None


class ValidationResult:
    """Represents a single validation result."""
    def __init__(self, rule_id: str, rule_name: str, severity: str,
                 passed: bool, message: str):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.severity = severity
        self.passed = passed
        self.message = message


class CoreValidator:
    """Config-driven validator with multi-error aggregation."""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).resolve().parent / "validator_config.yaml"
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML config or return empty dict if unavailable."""
        if yaml is None:
            print("WARNING: PyYAML not installed. Using fallback rules.")
            return {}
        if not self.config_path.exists():
            print(f"WARNING: Config not found: {self.config_path}")
            return {}
        with open(self.config_path, encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _get_profile_rules(self, profile: str) -> List[str]:
        """Get all rule IDs for a profile, including inherited."""
        profiles = self.config.get('profiles', {})
        if profile not in profiles:
            return []

        prof = profiles[profile]
        rules = list(prof.get('rules', []))

        # Handle inheritance
        if 'inherit' in prof:
            parent_rules = self._get_profile_rules(prof['inherit'])
            rules = parent_rules + rules

        return rules

    def _check_rule(self, rule_id: str, content: str) -> ValidationResult:
        """Check a single rule against content."""
        rules = self.config.get('rules', {})
        if rule_id not in rules:
            return ValidationResult(rule_id, rule_id, "error", True, "")

        rule = rules[rule_id]
        name = rule.get('name', rule_id)
        severity = rule.get('severity', 'error')
        message = rule.get('message', f"Rule {rule_id} failed.")
        triggers = rule.get('triggers', [])
        always_check = rule.get('always_check', False)
        content_lower = content.lower()

        # Check if rule should be applied
        triggered = always_check
        if not triggered and triggers:
            triggered = any(t.lower() in content_lower for t in triggers)

        if not triggered:
            # Rule not applicable
            return ValidationResult(rule_id, name, severity, True, "")

        # Check requires_any
        if 'requires_any' in rule:
            found = False
            for req in rule['requires_any']:
                pattern = req.get('pattern', '')
                ptype = req.get('type', 'literal')
                if ptype == 'regex':
                    if re.search(pattern, content, re.IGNORECASE):
                        found = True
                        break
                else:
                    if pattern.lower() in content_lower:
                        found = True
                        break
            if not found:
                return ValidationResult(rule_id, name, severity, False, message)

        # Check requires_one_of (Simple list of regex patterns)
        if 'requires_one_of' in rule:
            found = False
            for pattern in rule['requires_one_of']:
                # Treat all as regex for flexibility
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
            if not found:
                return ValidationResult(rule_id, name, severity, False, message)

        # Check requires_before (ordering check)
        if 'requires_before' in rule:
            req_before = rule['requires_before']
            patterns = req_before.get('patterns', [])

            # Find first trigger position
            trigger_pos = len(content)
            for t in triggers:
                match = re.search(re.escape(t), content, re.IGNORECASE)
                if match:
                    trigger_pos = min(trigger_pos, match.start())

            # Check if any required pattern appears before trigger
            found_before = False
            for pat in patterns:
                match = re.search(re.escape(pat), content, re.IGNORECASE)
                if match and match.start() < trigger_pos:
                    found_before = True
                    break

            if not found_before:
                return ValidationResult(rule_id, name, severity, False, message)

        return ValidationResult(rule_id, name, severity, True, "")

    def validate(self, content: str, profile: str) -> Tuple[bool, List[ValidationResult]]:
        """
        Validate content against all rules for a profile.
        Returns (passed, results) where passed is False if any error-severity rule failed.
        """
        rule_ids = self._get_profile_rules(profile)
        results: List[ValidationResult] = []

        for rule_id in rule_ids:
            result = self._check_rule(rule_id, content)
            results.append(result)

        # Determine overall pass/fail (only errors block, not warnings)
        has_error = any(not r.passed and r.severity == 'error' for r in results)
        return (not has_error, results)

    def print_results(self, results: List[ValidationResult]) -> None:
        """Print all validation results."""
        errors = [r for r in results if not r.passed and r.severity == 'error']
        warnings = [r for r in results if not r.passed and r.severity == 'warning']

        if errors:
            print("=" * 60)
            print("VALIDATION ERRORS (Must Fix)")
            print("=" * 60)
            for r in errors:
                print(f"❌ [{r.rule_name}]: {r.message}")
            print()

        if warnings:
            print("-" * 60)
            print("WARNINGS (Recommended)")
            print("-" * 60)
            for r in warnings:
                print(f"⚠️ [{r.rule_name}]: {r.message}")
            print()

        if not errors and not warnings:
            print("✅ Validation Passed: All checks compliant.")


def validate_file(filepath: str, profile: str) -> int:
    """
    Main entry point for file validation.
    Returns exit code (0 = pass, 1 = fail).
    """
    try:
        with open(filepath, encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"ERROR: Could not read file: {e}")
        return 1

    validator = CoreValidator()
    passed, results = validator.validate(content, profile)
    validator.print_results(results)

    return 0 if passed else 1


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: core_validator.py <filepath> <profile>")
        print("Profiles: debug, debug_lite, debug_strict, rca, rca_lite, rca_strict, dne")
        sys.exit(1)

    filepath = sys.argv[1]
    profile = sys.argv[2]
    sys.exit(validate_file(filepath, profile))
