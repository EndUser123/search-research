"""
Competence Layer - Task Type Registry
====================================

Central registry for task types, output contracts, and competence templates.
Maps skills to task types and provides reasoning guidance per task type.
"""

from .task_type_registry import (
    META_TASK_TYPE,
    check_contract_completeness,
    # Field detection
    check_field_present,
    # Competence templates
    get_competence_template,
    # Enforcement mode
    get_enforcement_mode,
    get_optional_fields,
    # Output contracts
    get_output_contract,
    get_required_fields,
    # Task type resolution
    get_task_type_for_skill,
    # Core loading
    load_registry,
    render_template,
)

__all__ = [
    # Core loading
    "load_registry",
    # Task type resolution
    "get_task_type_for_skill",
    "META_TASK_TYPE",
    # Output contracts
    "get_output_contract",
    "get_required_fields",
    "get_optional_fields",
    # Enforcement mode
    "get_enforcement_mode",
    # Competence templates
    "get_competence_template",
    "render_template",
    # Field detection
    "check_field_present",
    "check_contract_completeness",
]
