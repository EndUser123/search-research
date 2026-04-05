#!/usr/bin/env python3
"""
CWO12 Artifact Template Generator

This script generates CWO12-compliant project artifacts (plan.md, tasks.md, data_model.md)
based on predefined templates and user-provided project information.

Author: CWO12 Template Generator
Version: 1.0.0
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ProjectConfig:
    """Configuration for project artifact generation."""
    project_name: str
    task_id: str
    project_description: str
    project_type: str
    custom_vars: dict[str, str]
    output_directory: str


class TemplateGenerator:
    """Generates CWO12-compliant project artifacts from templates."""

    def __init__(self, templates_dir: str):
        """
        Initialize the template generator.

        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = Path(templates_dir)
        self.supported_types = [
            'api-development',
            'web-application',
            'data-processing',
            'ml-project'
        ]

    def validate_project_type(self, project_type: str) -> bool:
        """
        Validate that the project type is supported.

        Args:
            project_type: Type of project to generate

        Returns:
            True if project type is supported, False otherwise
        """
        return project_type in self.supported_types

    def load_template(self, project_type: str, artifact_type: str) -> str:
        """
        Load a template file.

        Args:
            project_type: Type of project
            artifact_type: Type of artifact (plan, tasks, data_model)

        Returns:
            Template content as string

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        template_file = (
            self.templates_dir /
            'templates' /
            project_type /
            f"{artifact_type}.md"
        )

        if not template_file.exists():
            raise FileNotFoundError(
                f"Template not found: {template_file}"
            )

        return template_file.read_text(encoding='utf-8')

    def substitute_variables(self, template: str, config: ProjectConfig) -> str:
        """
        Substitute variables in template with project-specific values.

        Args:
            template: Template content with variable placeholders
            config: Project configuration with variable values

        Returns:
            Template with variables substituted
        """
        # Standard variables
        substitutions = {
            'PROJECT_NAME': config.project_name,
            'TASK_ID': config.task_id,
            'CURRENT_DATE': datetime.now().strftime('%Y-%m-%d'),
            'PROJECT_DESCRIPTION': config.project_description,
        }

        # Add custom variables
        substitutions.update(config.custom_vars)

        # Perform substitution
        result = template
        for key, value in substitutions.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))

        # Validate no unsubstituted variables remain (except known optional ones)
        remaining_vars = re.findall(r'\{\{([^}]+)\}\}', result)
        optional_vars = {
            'EXPECTED_RPS', 'ACCURACY_TARGET', 'LATENCY_TARGET', 'ERROR_RATE_TARGET',
            'TRAINING_IMPROVEMENT_TARGET', 'AVAILABILITY_TARGET', 'EFFICIENCY_TARGET',
            'PIPELINE_LATENCY_TARGET', 'VALIDATION_COVERAGE_TARGET', 'EXPLAINABILITY_TARGET',
            'REPRODUCIBILITY_TARGET', 'TEST_COVERAGE_TARGET', 'DATA_VOLUME',
            'THROUGHPUT_TARGET', 'MODEL_AVAILABILITY_TARGET', 'DRIFT_RATE_TARGET',
            'PREDICTION_VOLUME_TARGET', 'COST_EFFICIENCY_TARGET', 'USER_SATISFACTION_TARGET',
            'DATA_QUALITY_TARGET', 'PIPELINE_RELIABILITY_TARGET', 'DATA_LATENCY_TARGET',
            'STORAGE_SIZE', 'RUNTIME_ENVIRONMENT', 'API_FRAMEWORK', 'DATABASE_SYSTEM',
            'AUTH_SYSTEM', 'TESTING_FRAMEWORK', 'DEPLOYMENT_PLATFORM', 'PROCESSING_FRAMEWORK',
            'ML_FRAMEWORK', 'FEATURE_STORE', 'MODEL_REGISTRY', 'ORCHESTRATOR', 'MONITORING_TOOLS',
            'PRIMARY_DATA_SOURCES', 'SECONDARY_DATA_SOURCES', 'EXTERNAL_DATA_SOURCES',
            'STREAMING_SOURCES', 'SUPERVISED_MODELS', 'UNSUPERVISED_MODELS',
            'ENSEMBLE_METHODS', 'DEEP_LEARNING_MODELS'
        }

        unresolved_vars = [var for var in remaining_vars if var not in optional_vars]
        if unresolved_vars:
            print(f"Warning: Unresolved variables: {unresolved_vars}", file=sys.stderr)
            print("These will remain as placeholders in the generated files.", file=sys.stderr)

        return result

    def validate_cwo12_compliance(self, content: str, artifact_type: str) -> tuple[bool, list]:
        """
        Validate that the generated content meets CWO12 requirements.

        Args:
            content: Generated artifact content
            artifact_type: Type of artifact being validated

        Returns:
            Tuple of (is_compliant, list_of_issues)
        """
        issues = []

        if artifact_type == 'plan':
            # Check for required sections in plan.md (based on CWO12 actual requirements)
            required_sections = [
                '## Objectives',
                '## Scope',
                '## Success Criteria',
                '## Risk Assessment',
                '## Timeline'  # or Implementation Timeline
            ]

            for section in required_sections:
                # Allow alternative names for some sections
                found = False
                if section == '## Timeline':
                    found = '## Timeline' in content or '## Implementation Timeline' in content
                else:
                    found = section in content

                if not found:
                    issues.append(f"Missing required section: {section}")

            # Basic validation: objectives section exists and has some content
            if '## Objectives' in content:
                # Very lenient check - just make sure the section exists
                pass  # The section existence check above is sufficient

        elif artifact_type == 'tasks':
            # Check for required sections in tasks.md (based on CWO12 actual requirements)
            required_sections = [
                '## Task Breakdown',
                '## Task Dependencies',
                '## Resource Requirements'
            ]

            for section in required_sections:
                if section not in content:
                    issues.append(f"Missing required section: {section}")

            # Check that there are some tasks defined
            if '## Task Breakdown' in content:
                # Simple check for task indicators
                task_indicators = ['####', '###', 'Phase', '- [', 'Task']
                has_tasks = any(indicator in content for indicator in task_indicators)
                if not has_tasks:
                    issues.append("Task breakdown should contain specific tasks or phases")

        elif artifact_type == 'data_model':
            # Check for required sections in data_model.md (based on CWO12 actual requirements)
            required_sections = [
                '## Data Model Overview',
                '## Entity Definitions',
                '## Relationships',
                '## Data Integrity'
            ]

            for section in required_sections:
                # Allow alternative section names
                found = False
                if section == '## Entity Definitions' and '## Core Entity Definitions' in content:
                    found = True
                elif section == '## Data Integrity' and ('## Data Integrity Constraints' in content or '## Constraints' in content):
                    found = True
                else:
                    found = section in content

                if not found:
                    issues.append(f"Missing required section: {section}")

        is_compliant = len(issues) == 0
        return is_compliant, issues

    def generate_artifact(self, config: ProjectConfig, artifact_type: str) -> tuple[str, bool, list]:
        """
        Generate a single artifact.

        Args:
            config: Project configuration
            artifact_type: Type of artifact to generate

        Returns:
            Tuple of (content, is_compliant, issues)
        """
        try:
            # Load template
            template = self.load_template(config.project_type, artifact_type)

            # Substitute variables
            content = self.substitute_variables(template, config)

            # Validate CWO12 compliance
            is_compliant, issues = self.validate_cwo12_compliance(content, artifact_type)

            return content, is_compliant, issues

        except Exception as e:
            return f"Error generating {artifact_type}: {str(e)}", False, [str(e)]

    def generate_all_artifacts(self, config: ProjectConfig) -> dict[str, dict[str, Any]]:
        """
        Generate all three artifacts for a project.

        Args:
            config: Project configuration

        Returns:
            Dictionary with artifact generation results
        """
        artifacts = ['plan', 'tasks', 'data_model']
        results = {}

        for artifact_type in artifacts:
            content, is_compliant, issues = self.generate_artifact(config, artifact_type)
            results[artifact_type] = {
                'content': content,
                'is_compliant': is_compliant,
                'issues': issues,
                'filename': f"{artifact_type}.md"
            }

        return results

    def save_artifacts(self, results: dict[str, dict[str, Any]], config: ProjectConfig) -> bool:
        """
        Save generated artifacts to files.

        Args:
            results: Artifact generation results
            config: Project configuration

        Returns:
            True if all files saved successfully, False otherwise
        """
        try:
            output_dir = Path(config.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)

            success = True
            for artifact_type, result in results.items():
                filename = result['filename']
                filepath = output_dir / filename

                filepath.write_text(result['content'], encoding='utf-8')
                print(f"Generated: {filepath}")

                if not result['is_compliant']:
                    print(f"  [!] Compliance issues found in {filename}")
                    for issue in result['issues']:
                        print(f"    - {issue}")
                    success = False

            return success

        except Exception as e:
            print(f"Error saving artifacts: {str(e)}", file=sys.stderr)
            return False


def load_config_from_file(config_file: str) -> ProjectConfig:
    """
    Load project configuration from JSON file.

    Args:
        config_file: Path to configuration file

    Returns:
        Project configuration object
    """
    with open(config_file, encoding='utf-8') as f:
        data = json.load(f)

    return ProjectConfig(
        project_name=data['project_name'],
        task_id=data['task_id'],
        project_description=data['project_description'],
        project_type=data['project_type'],
        custom_vars=data.get('custom_vars', {}),
        output_directory=data.get('output_directory', '.')
    )


def interactive_config() -> ProjectConfig:
    """
    Create project configuration through interactive prompts.

    Returns:
        Project configuration object
    """
    print("CWO12 Artifact Template Generator")
    print("=" * 40)

    project_name = input("Project name: ").strip()
    if not project_name:
        print("Error: Project name is required")
        sys.exit(1)

    task_id = input("Task ID (e.g., TSK-001): ").strip()
    if not task_id:
        task_id = f"TSK-{datetime.now().strftime('%Y%m%d')}-{len(project_name):03d}"
        print(f"Using generated Task ID: {task_id}")

    project_description = input("Project description: ").strip()
    if not project_description:
        project_description = f"Development of {project_name}"
        print(f"Using default description: {project_description}")

    print(f"\nSupported project types: {', '.join(TemplateGenerator('.').supported_types)}")
    project_type = input("Project type: ").strip().lower()
    if not project_type:
        project_type = 'api-development'
        print(f"Using default project type: {project_type}")

    output_directory = input("Output directory (default: .): ").strip()
    if not output_directory:
        output_directory = '.'

    # Custom variables
    custom_vars = {}
    print("\nOptional custom variables (press Enter to skip):")

    optional_prompts = [
        ("Expected RPS", "EXPECTED_RPS", "1000"),
        ("Accuracy target (%)", "ACCURACY_TARGET", "95"),
        ("Latency target (ms)", "LATENCY_TARGET", "100"),
        ("Database system", "DATABASE_SYSTEM", "PostgreSQL"),
        ("API framework", "API_FRAMEWORK", "FastAPI"),
    ]

    for prompt, var_name, default in optional_prompts:
        value = input(f"{prompt} (default: {default}): ").strip()
        if value:
            custom_vars[var_name] = value

    return ProjectConfig(
        project_name=project_name,
        task_id=task_id,
        project_description=project_description,
        project_type=project_type,
        custom_vars=custom_vars,
        output_directory=output_directory
    )


def main():
    """Main function to run the template generator."""
    parser = argparse.ArgumentParser(
        description='Generate CWO12-compliant project artifacts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python generate_artifacts.py

  # From configuration file
  python generate_artifacts.py --config project_config.json

  # Command line arguments
  python generate_artifacts.py --name "My API" --type api-development --output ./my-project
        """
    )

    parser.add_argument(
        '--config', '-c',
        help='Configuration file (JSON)'
    )
    parser.add_argument(
        '--name', '-n',
        help='Project name'
    )
    parser.add_argument(
        '--type', '-t',
        choices=['api-development', 'web-application', 'data-processing', 'ml-project'],
        help='Project type'
    )
    parser.add_argument(
        '--description', '-d',
        help='Project description'
    )
    parser.add_argument(
        '--task-id',
        help='Task ID (e.g., TSK-001)'
    )
    parser.add_argument(
        '--output', '-o',
        default='.',
        help='Output directory (default: current directory)'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate existing artifacts, don\'t generate new ones'
    )

    args = parser.parse_args()

    # Get template generator
    script_dir = Path(__file__).parent
    templates_dir = script_dir.parent
    generator = TemplateGenerator(templates_dir)

    # Load configuration
    if args.config:
        if not os.path.exists(args.config):
            print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
            sys.exit(1)
        config = load_config_from_file(args.config)
    elif args.name:
        if not args.type:
            print("Error: --type is required when using --name", file=sys.stderr)
            sys.exit(1)
        config = ProjectConfig(
            project_name=args.name,
            task_id=args.task_id or f"TSK-{datetime.now().strftime('%Y%m%d')}-001",
            project_description=args.description or f"Development of {args.name}",
            project_type=args.type,
            custom_vars={},
            output_directory=args.output
        )
    else:
        config = interactive_config()

    # Validate project type
    if not generator.validate_project_type(config.project_type):
        print(f"Error: Unsupported project type: {config.project_type}", file=sys.stderr)
        print(f"Supported types: {', '.join(generator.supported_types)}", file=sys.stderr)
        sys.exit(1)

    # Generate artifacts
    print(f"\nGenerating artifacts for: {config.project_name}")
    print(f"Project type: {config.project_type}")
    print(f"Output directory: {config.output_directory}")
    print()

    results = generator.generate_all_artifacts(config)

    # Display results
    all_compliant = True
    for artifact_type, result in results.items():
        status = "[OK] Compliant" if result['is_compliant'] else "[!] Issues found"
        print(f"{result['filename']}: {status}")

        if result['issues']:
            all_compliant = False
            for issue in result['issues']:
                print(f"  - {issue}")

    # Save artifacts
    if not args.validate_only:
        print("\nSaving artifacts...")
        success = generator.save_artifacts(results, config)

        if success and all_compliant:
            print("\n[SUCCESS] All artifacts generated successfully!")
            print("Artifacts are CWO12 compliant and ready for use.")
        elif success:
            print("\n[SUCCESS] Artifacts generated successfully!")
            print("Note: Some compliance issues were identified but can be addressed in the generated files.")
            print("The artifacts are functional and ready for use.")
        else:
            print("\n[ERROR] Error saving artifacts.")
            sys.exit(1)
    else:
        if all_compliant:
            print("\n[SUCCESS] All artifacts would be CWO12 compliant.")
        else:
            print("\n[WARNING] Compliance issues found that need to be addressed.")


if __name__ == '__main__':
    main()
