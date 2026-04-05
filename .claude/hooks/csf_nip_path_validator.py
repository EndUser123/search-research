#!/usr/bin/env python3
from __future__ import annotations

"""
CSF NIP Path Validator Extension
"""

import fnmatch
from pathlib import Path
from typing import Any

from __lib.path_validator import PathValidator


class CSFNIPPathValidator(PathValidator):
    """Extends PathValidator for __csf directory validation."""

    def __init__(self, config_path: Path | None = None):
        super().__init__(config_path)
        self._build_csf_validation_rules()

    def _build_csf_validation_rules(self) -> None:
        """Build validation rule sets from extended policy."""
        policy = self.policy.get_full_config()
        csf_policy = policy.get("csf_nip_directory", {})

        self.csf_hidden_dirs = set(
            d["path"] for d in csf_policy.get("allowed_hidden_directories", [])
        )
        self.csf_operational_dirs = set(
            d["path"] for d in csf_policy.get("allowed_operational_directories", [])
        )
        self.csf_questionable_dirs = set(
            d["path"] for d in csf_policy.get("questionable_directories", [])
        )
        self.consolidation_rules = csf_policy.get("consolidation_rules", [])

        self.hidden_dir_purposes = {
            d["path"]: d.get("purpose", "")
            for d in csf_policy.get("allowed_hidden_directories", [])
        }
        self.operational_dir_purposes = {
            d["path"]: d.get("purpose", "")
            for d in csf_policy.get("allowed_operational_directories", [])
        }
        self.questionable_dir_purposes = {
            d["path"]: d.get("purpose", "")
            for d in csf_policy.get("questionable_directories", [])
        }

    def validate_csf_nip_operation(self, file_path: str) -> dict[str, Any]:
        """Validate file operation within __csf/."""
        path = Path(file_path)
        norm_path = self.normalize_path(str(path))

        if not norm_path.startswith("p:/__csf/"):
            return {
                "is_safe": False, "violation_type": "OUT_OF_SCOPE",
                "suggestion": "This validator only handles __csf/ paths",
                "can_approve": False, "category": None, "directory": None
            }

        parts = Path(norm_path).relative_to("p:/__csf/").parts
        if not parts:
            dir_name = ""
            is_root_level = True
        else:
            dir_name = parts[0]
            # Nested = more than one directory level (e.g., "src/subdir/file.txt")
            # A file within a single-level directory (e.g., ".cache/file.txt") is NOT nested
            is_root_level = (len(parts) <= 2)

        if len(parts) > 2:
            # More than one directory level = nested (e.g., src/core/utils/file.py has 3 parts)
            return {
                "is_safe": True, "violation_type": None, "suggestion": None,
                "can_approve": False, "category": "nested", "directory": dir_name
            }

        for pattern_info in self.policy.get_csf_blocked_patterns():
            pattern = pattern_info["pattern"]
            if fnmatch.fnmatch(path.name, pattern):
                return {
                    "is_safe": False, "violation_type": "BLOCKED_PATTERN",
                    "suggestion": pattern_info.get("suggestion", ""),
                    "can_approve": False, "category": "blocked", "directory": dir_name
                }

        allowed_subdirs = set(d["path"] for d in self.policy.get_csf_allowed_subdirs())
        if dir_name in allowed_subdirs:
            return {
                "is_safe": True, "violation_type": None, "suggestion": None,
                "can_approve": False, "category": "subdirectory", "directory": dir_name
            }

        if dir_name in self.csf_hidden_dirs:
            return {
                "is_safe": True, "violation_type": None, "suggestion": None,
                "can_approve": False, "category": "hidden", "directory": dir_name
            }

        if dir_name in self.csf_operational_dirs:
            return {
                "is_safe": True, "violation_type": None, "suggestion": None,
                "can_approve": False, "category": "operational", "directory": dir_name
            }

        if dir_name in self.csf_questionable_dirs:
            return {
                "is_safe": False, "violation_type": "QUESTIONABLE",
                "suggestion": self.questionable_dir_purposes.get(dir_name, "Manual review required"),
                "can_approve": False, "category": "questionable", "directory": dir_name
            }

        return {
            "is_safe": False, "violation_type": "UNKNOWN_DIR",
            "suggestion": f"Directory '{dir_name}' is not in the allowed list",
            "can_approve": True, "category": "unknown", "directory": dir_name
        }

    def get_all_allowed_directories(self) -> set[str]:
        allowed = set()
        allowed.update(d["path"] for d in self.policy.get_csf_allowed_subdirs())
        allowed.update(self.csf_hidden_dirs)
        allowed.update(self.csf_operational_dirs)
        return allowed

    def get_consolidation_rules(self) -> list[dict[str, Any]]:
        return self.consolidation_rules.copy()

    def get_directory_purpose(self, dir_name: str) -> str | None:
        if dir_name in self.hidden_dir_purposes:
            return self.hidden_dir_purposes[dir_name]
        if dir_name in self.operational_dir_purposes:
            return self.operational_dir_purposes[dir_name]
        if dir_name in self.questionable_dir_purposes:
            return self.questionable_dir_purposes[dir_name]
        for d in self.policy.get_csf_allowed_subdirs():
            if d["path"] == dir_name:
                return d.get("purpose", "")
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CSF NIP Path Validator")
    parser.add_argument("path", nargs="?", help="Path to validate")
    parser.add_argument("--list-allowed", action="store_true", help="List all allowed directories")
    parser.add_argument("--list-consolidation", action="store_true", help="List consolidation rules")
    parser.add_argument("--check-dir", help="Check if a directory name is allowed")
    args = parser.parse_args()

    validator = CSFNIPPathValidator()

    if args.list_allowed:
        print("Allowed directories at __csf/ root:")
        for d in sorted(validator.get_all_allowed_directories()):
            purpose = validator.get_directory_purpose(d)
            print(f"  {d}/ - {purpose}" if purpose else f"  {d}/")

    elif args.list_consolidation:
        print("Consolidation rules:")
        for rule in validator.get_consolidation_rules():
            print(f"  Sources: {', '.join(rule['sources'])}")
            print(f"  Target: {rule['target']}/")
            print(f"  Priority: {rule['priority']}")
            print(f"  Reason: {rule['reason']}")
            print()

    elif args.check_dir:
        result = validator.validate_csf_nip_operation(f"P:/__csf/{args.check_dir}/dummy.txt")
        if result["is_safe"]:
            print(f"✅ '{args.check_dir}' is ALLOWED (category: {result['category']})")
        else:
            print(f"❌ '{args.check_dir}' is {result['violation_type']}")
            print(f"   Suggestion: {result['suggestion']}")

    elif args.path:
        result = validator.validate_csf_nip_operation(args.path)
        print(f"Path: {args.path}")
        print(f"Safe: {result['is_safe']}")
        if result['violation_type']:
            print(f"Violation: {result['violation_type']}")
            print(f"Suggestion: {result['suggestion']}")
            print(f"Can approve: {result['can_approve']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
