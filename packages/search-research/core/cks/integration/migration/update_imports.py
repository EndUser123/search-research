import argparse
import re
from pathlib import Path

"""Migration script to update import references for CKS integration refactoring.

This script helps update existing modules to use the new centralized CKS integration
interface instead of the scattered integration files.

Usage:
    python update_imports.py --scan          # Scan for files that need updating
    python update_imports.py --update        # Update files (dry run by default)
    python update_imports.py --apply         # Apply changes permanently
"""


class ImportUpdater:
    """Updates import statements for CKS integration refactoring."""

    # Mapping of old import patterns to new usage patterns
    MIGRATION_MAP = {
        # Constitutional Compliance
        "from modules.constitutional_compliance.cks_compliance_monitor import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.CONSTITUTIONAL_COMPLIANCE",
        },
        "from modules.constitutional_compliance.cks_constitutional_compliance_validator import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.CONSTITUTIONAL_COMPLIANCE",
        },
        "from modules.constitutional_compliance.cwo12_cks_compliance_validator import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.CONSTITUTIONAL_COMPLIANCE",
        },
        # Orchestration
        "from modules.orchestration.cks_agent_coordinator import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.ORCHESTRATION",
        },
        # Monitoring
        "from modules.monitoring.cks_monitoring_analytics import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.MONITORING",
        },
        # Performance
        "from modules.performance.cks_performance_optimizer import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.PERFORMANCE",
        },
        # Task Management
        "from modules.task_management.cks_integration import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.TASK_MANAGEMENT",
        },
        # Knowledge System
        "from modules.knowledge_system.cks_constitutional_validator import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.KNOWLEDGE_SYSTEM",
        },
        "from modules.knowledge_system.cks_input_validator import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.KNOWLEDGE_SYSTEM",
        },
        # Resilience
        "from modules.resilience.cks_fallback_error_handler import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.RESILIENCE",
        },
        # Universal Instrumentation
        "from modules.universal_instrumentation.integrations.cks_error_recovery_system import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.UNIVERSAL_INSTRUMENTATION",
        },
        "from modules.universal_instrumentation.integrations.cks_instrumentation import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.UNIVERSAL_INSTRUMENTATION",
        },
        "from modules.universal_instrumentation.integrations.cks_rag_integration_coordinator import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.UNIVERSAL_INSTRUMENTATION",
        },
        "from modules.universal_instrumentation.integrations.cks_session_integration_coordinator import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.UNIVERSAL_INSTRUMENTATION",
        },
        # Other integrations
        "from modules.automated_fix_suggestions.integration.cks_integration import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.AUTOMATED_FIX_SUGGESTIONS",
        },
        "from modules.integration.cks_tasks_9_12_integration import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.INTEGRATION",
        },
        "from modules.unified_systems.evidence.cks_integration import": {
            "new_import": "from ...integration import IntegrationType, cks_integration_manager",
            "usage_pattern": "IntegrationType.UNIFIED_SYSTEMS",
        },
    }

    def __init__(self, project_root: Path) -> None:
        """Initialize the import updater.

        Args:
            project_root: Root path of the project

        """
        self.project_root = project_root
        self.files_needing_update: list[dict[str, str]] = []

    def scan_for_migration_candidates(self, directory: Path) -> list[dict[str, str]]:
        """Scan directory for files that need migration.

        Args:
            directory: Directory to scan

        Returns:
            List of files that need updating

        """
        candidates = []

        for file_path in directory.rglob("*.py"):
            if "cks" in file_path.name.lower() or "integration" in file_path.name.lower():
                continue  # Skip CKS integration files themselves

            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                for i, line in enumerate(lines):
                    for old_import_pattern in self.MIGRATION_MAP:
                        if old_import_pattern in line:
                            candidates.append(
                                {
                                    "file_path": str(file_path),
                                    "line_number": i + 1,
                                    "old_import": old_import_pattern,
                                    "old_line": line.strip(),
                                    "migration_info": self.MIGRATION_MAP[old_import_pattern],
                                }
                            )
                            break

            except Exception as e:
                print(f"Error scanning {file_path}: {e}")

        self.files_needing_update = candidates
        return candidates

    def generate_migration_plan(self, candidates: list[dict[str, str]]) -> list[dict[str, str]]:
        """Generate migration plan for candidates.

        Args:
            candidates: List of files needing update

        Returns:
            Migration plan with suggested changes

        """
        migration_plan = []

        for candidate in candidates:
            file_path = Path(candidate["file_path"])
            relative_path = file_path.relative_to(self.project_root)

            # Generate new import statement
            old_class_match = re.search(r"from .* import (\w+)", candidate["old_line"])
            if old_class_match:
                old_class_name = old_class_match.group(1)
                new_import_line = candidate["migration_info"]["new_import"]

                # Suggest new usage pattern
                usage_pattern = candidate["migration_info"]["usage_pattern"]

                migration_plan.append(
                    {
                        "file": str(relative_path),
                        "line_number": candidate["line_number"],
                        "old_import": candidate["old_line"],
                        "new_import": new_import_line,
                        "old_class": old_class_name,
                        "usage_pattern": usage_pattern,
                        "requires_manual_review": True,
                    }
                )

        return migration_plan

    def update_file(self, file_path: Path, line_number: int, old_line: str, new_line: str) -> bool:
        """Update a specific line in a file.

        Args:
            file_path: File to update
            line_number: Line number (1-based)
            old_line: Old line content
            new_line: New line content

        Returns:
            True if successful, False otherwise

        """
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            if line_number > len(lines):
                return False

            # Update the specific line
            lines[line_number - 1] = new_line + "\n"

            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            return True

        except Exception as e:
            print(f"Error updating {file_path}: {e}")
            return False

    def create_migration_guide(self, candidates: list[dict[str, str]]) -> str:
        """Create a migration guide for developers.

        Args:
            candidates: List of files needing update

        Returns:
            Migration guide content

        """
        guide = []
        guide.append("# CKS Integration Migration Guide")
        guide.append("=" * 50)
        guide.append("")
        guide.append("This guide shows how to migrate from scattered CKS integration files")
        guide.append("to the new centralized CKS integration system.")
        guide.append("")
        guide.append("## Migration Steps")
        guide.append("")
        guide.append("### 1. Update Imports")
        guide.append("")
        guide.append("Replace old scattered imports:")
        guide.append("")

        unique_files = {candidate["file"] for candidate in candidates}

        for file_path in sorted(unique_files):
            file_candidates = [c for c in candidates if c["file"] == file_path]
            guide.append(f"#### File: {file_path}")
            guide.append("")

            for candidate in file_candidates:
                guide.append(f"**Old (Line {candidate['line_number']}):**")
                guide.append("```python")
                guide.append(candidate["old_line"])
                guide.append("```")
                guide.append("")
                guide.append("**New:**")
                guide.append("```python")
                guide.append(candidate["migration_info"]["new_import"])
                guide.append("```")
                guide.append("")

                # Add usage example
                guide.append("**Usage Example:**")
                guide.append("```python")
                guide.append("# Initialize once at startup")
                guide.append("from ...integration import csf.cks_integration_manager")
                guide.append("cks_integration_manager.initialize_all_integrations()")
                guide.append("")
                guide.append("# Use the integration")
                guide.append("result = cks_integration_manager.process_with_integration(")
                guide.append(f"    {candidate['migration_info']['usage_pattern']},")
                guide.append("    operation_data={'action': 'validate'}")
                guide.append(")")
                guide.append("```")
                guide.append("")

        guide.append("### 2. Update Usage Patterns")
        guide.append("")
        guide.append("Replace direct class instantiation:")
        guide.append("```python")
        guide.append("# OLD")
        guide.append(
            "from modules.monitoring.cks_monitoring_analytics import CKSMonitoringAnalytics"
        )
        guide.append("monitor = CKSMonitoringAnalytics()")
        guide.append("result = monitor.process(data)")
        guide.append("")
        guide.append("# NEW")
        guide.append("from ...integration import IntegrationType, cks_integration_manager")
        guide.append("result = cks_integration_manager.process_with_integration(")
        guide.append("    IntegrationType.MONITORING,")
        guide.append("    operation_data=data")
        guide.append(")")
        guide.append("```")
        guide.append("")

        return "\n".join(guide)


def main() -> None:
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(description="Update CKS integration imports")
    parser.add_argument("--scan", action="store_true", help="Scan for files needing updates")
    parser.add_argument("--update", action="store_true", help="Show update plan (dry run)")
    parser.add_argument("--apply", action="store_true", help="Apply changes permanently")
    parser.add_argument("--guide", action="store_true", help="Generate migration guide")
    parser.add_argument("--directory", default="src/features/modules", help="Directory to scan")

    args = parser.parse_args()

    if not any([args.scan, args.update, args.apply, args.guide]):
        parser.print_help()
        return

    # Get project root
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    target_directory = project_root / args.directory

    print(f"Project root: {project_root}")
    print(f"Scanning directory: {target_directory}")
    print()

    updater = ImportUpdater(project_root)

    # Scan for candidates
    print("🔍 Scanning for files needing migration...")
    candidates = updater.scan_for_migration_candidates(target_directory)

    if not candidates:
        print("✅ No files found that need migration!")
        return

    print(f"📊 Found {len(candidates)} import statements that need updating:")
    print()

    # Show candidates
    for candidate in candidates[:10]:  # Show first 10
        relative_path = Path(candidate["file_path"]).relative_to(project_root)
        print(f"  📄 {relative_path}:{candidate['line_number']}")
        print(f"     {candidate['old_line']}")
        print()

    if len(candidates) > 10:
        print(f"  ... and {len(candidates) - 10} more")
        print()

    if args.scan:
        print(f"Scan complete. {len(candidates)} files need migration.")
        return

    # Generate migration plan
    if args.update or args.apply:
        migration_plan = updater.generate_migration_plan(candidates)

        print("📋 Migration Plan:")
        print("=" * 50)
        for plan_item in migration_plan:
            print(f"📄 {plan_item['file']}:{plan_item['line_number']}")
            print(f"   Old: {plan_item['old_import']}")
            print(f"   New: {plan_item['new_import']}")
            print()

        if args.update:
            print("💡 Dry run complete. Use --apply to make changes.")
            return

        if args.apply:
            print("🚀 Applying changes...")
            updated_count = 0

            for plan_item in migration_plan:
                file_path = project_root / plan_item["file"]
                success = updater.update_file(
                    file_path,
                    plan_item["line_number"],
                    plan_item["old_line"],
                    plan_item["new_import"],
                )

                if success:
                    print(f"✅ Updated {plan_item['file']}:{plan_item['line_number']}")
                    updated_count += 1
                else:
                    print(f"❌ Failed to update {plan_item['file']}:{plan_item['line_number']}")

            print(f"\n🎉 Migration complete! Updated {updated_count} files.")

    # Generate migration guide
    if args.guide:
        migration_guide = updater.create_migration_guide(candidates)

        guide_path = project_root / "CKS_MIGRATION_GUIDE.md"
        with open(guide_path, "w", encoding="utf-8") as f:
            f.write(migration_guide)

        print(f"📖 Migration guide created: {guide_path}")


if __name__ == "__main__":
    main()
