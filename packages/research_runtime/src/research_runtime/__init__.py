"""Green-field, harness-neutral research-run.v1 validation."""

from .validator import ValidationError, validate, validate_file, write_run
from .research_result import (
    ResearchResultValidationError,
    build_research_result,
    validate as validate_research_result,
    write_result,
)
from .decision_request import (
    DecisionRequestValidationError,
    validate as validate_decision_request,
    write_request,
)
from .decision_result import (
    DecisionResultValidationError,
    validate as validate_decision_result,
    write_result as write_decision_result,
)
from .design import synthesize as synthesize_design
from .brief import (
    ResearchBrief,
    BriefValidationError,
    build_brief,
    brief_from_dict,
    write_brief,
    TASK_CLASS_LOOKUP,
    TASK_CLASS_EXPLORATION,
    TASK_CLASS_IMPLEMENTATION,
    TASK_CLASS_DECISION_SUPPORT,
)

__all__ = [
    "ValidationError", "validate", "validate_file", "write_run",
    "ResearchResultValidationError", "build_research_result",
    "validate_research_result", "write_result",
    "DecisionRequestValidationError", "validate_decision_request", "write_request",
    "DecisionResultValidationError", "validate_decision_result", "write_decision_result",
    "synthesize_design",
    "ResearchBrief", "BriefValidationError",
    "build_brief", "brief_from_dict", "write_brief",
    "TASK_CLASS_LOOKUP", "TASK_CLASS_EXPLORATION",
    "TASK_CLASS_IMPLEMENTATION", "TASK_CLASS_DECISION_SUPPORT",
]
