# DUF6 Status Logic Enhancement Data Model

**Project:** TSK-031225-DUF6_Status_Logic_Fix
**Date:** 2025-12-03
**Version:** 1.0.0

## Entity Definitions

### ValidationStatus (Enhanced)
```python
class ValidationStatus(Enum):
    """Enhanced validation status distinguishing orchestration from quality."""

    # Orchestration Statuses (unchanged)
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

    # Quality Assessment Statuses (NEW)
    QUALITY_PASSED = "quality_passed"        # Code meets quality standards
    QUALITY_FAILED = "quality_failed"        # Code has quality issues
    QUALITY_WARNING = "quality_warning"      # Code has minor issues
    QUALITY_UNKNOWN = "quality_unknown"      # Unable to determine quality
```

### QualityGateConfig
```python
@dataclass
class QualityGateConfig:
    """Configuration for validation quality gates."""

    # Severity thresholds
    max_critical_issues: int = 0            # Critical issues not allowed
    max_high_issues: int = 5                 # Allow up to 5 high issues
    max_medium_issues: int = 50              # Allow up to 50 medium issues
    max_low_issues: int = 200                # Allow up to 200 low issues

    # Percentage thresholds
    max_medium_percentage: float = 20.0      # Max 20% issues can be medium
    max_high_percentage: float = 5.0         # Max 5% issues can be high

    # File-based thresholds
    max_issues_per_file: int = 10            # Max issues per single file
    critical_file_exemptions: List[str] = None  # Files exempt from critical threshold

    # Scoring weights
    critical_weight: int = 10                # Critical = 10 points
    high_weight: int = 5                     # High = 5 points
    medium_weight: int = 2                   # Medium = 2 points
    low_weight: int = 1                      # Low = 1 point

    # Quality score thresholds
    min_quality_score: float = 80.0          # Minimum score to pass
    warning_quality_score: float = 60.0      # Below this = warning
```

### ValidationResult (Enhanced)
```python
@dataclass
class ValidationResult:
    """Enhanced validation result with separate orchestration and quality status."""

    validation_id: str
    orchestration_status: ValidationStatus    # Tool execution status
    quality_status: ValidationStatus          # Code quality assessment
    issues: List[ValidationIssue] = field(default_factory=list)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Quality assessment data (NEW)
    quality_score: float = 0.0                # Overall quality score (0-100)
    severity_breakdown: Dict[str, int] = field(default_factory=dict)
    quality_gate_config: QualityGateConfig = field(default_factory=QualityGateConfig)
    failed_quality_gates: List[str] = field(default_factory=list)
    quality_recommendations: List[str] = field(default_factory=list)
```

### QualityAssessment
```python
@dataclass
class QualityAssessment:
    """Detailed quality assessment results."""

    overall_score: float                      # 0-100 quality score
    severity_counts: Dict[SeverityLevel, int]  # Count by severity
    severity_percentages: Dict[SeverityLevel, float]  # Percentage by severity

    # Quality gate results
    gate_results: Dict[str, bool]             # Individual gate pass/fail
    failed_gates: List[str]                   # Names of failed gates

    # File-level analysis
    files_with_critical_issues: List[str]     # Files with critical issues
    files_with_high_issue_count: List[str]    # Files with many issues
    worst_files: List[Tuple[str, int]]        # (file_path, issue_count) top 10

    # Recommendations
    priority_recommendations: List[str]        # High-priority fixes
    quality_improvement_plan: Dict[str, Any]  # Structured improvement plan
```

### ValidationIssue (Enhanced)
```python
@dataclass
class ValidationIssue:
    """Enhanced validation issue with quality impact assessment."""

    issue_id: str
    title: str
    description: str
    severity: SeverityLevel
    component: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    # Quality impact assessment (NEW)
    quality_impact_score: float = 0.0        # Impact on overall quality score
    fix_effort: str = "unknown"               # Estimated fix effort (low/medium/high)
    fix_priority: int = 0                     # Priority level (1-10)
    auto_fixable: bool = False                # Can be automatically fixed
```

## Relationships

### Primary Relationships

```
ValidationResult
├── orchestration_status (ValidationStatus)
├── quality_status (ValidationStatus)
├── quality_gate_config (QualityGateConfig)
├── quality_assessment (QualityAssessment)
└── issues (List[ValidationIssue])
    └── quality_impact_score (float)
```

### Quality Assessment Flow

```
ValidationIssue List
    ↓
QualityAssessment Engine
    ↓ (calculates)
QualityAssessment
    ↓ (applies gates)
QualityGateConfig
    ↓ (determines)
quality_status: ValidationStatus
```

### Template Data Flow

```
ValidationResult
    ↓ (enhanced data)
DeveloperTemplate
    ↓ (displays)
- Orchestration Status: "COMPLETED"
- Quality Status: "QUALITY_FAILED"
- Quality Score: 45.2/100
- Failed Gates: ["max_critical_issues", "quality_score_threshold"]
```

## Data Integrity Rules

### ValidationStatus Consistency
- `orchestration_status` must be COMPLETED before `quality_status` is evaluated
- If `orchestration_status` is FAILED, `quality_status` must be QUALITY_UNKNOWN
- QUALITY_PASSED requires `quality_score >= min_quality_score`

### QualityGateConfig Validation
- Threshold values must be non-negative integers
- Percentage thresholds must be between 0-100
- Critical threshold must be 0 (critical issues not allowed in production)

### Quality Score Calculation
```
quality_score = max(0, 100 - (
    (critical_issues * 10) +      # Critical = 10 points each
    (high_issues * 5) +          # High = 5 points each
    (medium_issues * 2) +        # Medium = 2 points each
    (low_issues * 1)              # Low = 1 point each
))
```

### Severity Breakdown Requirements
- Must include counts for all severity levels
- Percentages must sum to 100%
- Critical percentage must match critical count/total_count

## Configuration Schema

### Quality Gate Configuration
```json
{
  "quality_gates": {
    "max_critical_issues": 0,
    "max_high_issues": 5,
    "max_medium_issues": 50,
    "max_low_issues": 200,
    "max_medium_percentage": 20.0,
    "max_high_percentage": 5.0,
    "max_issues_per_file": 10,
    "min_quality_score": 80.0,
    "warning_quality_score": 60.0
  },
  "severity_weights": {
    "critical": 10,
    "high": 5,
    "medium": 2,
    "low": 1
  }
}
```

## Validation Rules

### Business Rules
1. **Critical Issue Rule**: Any critical issues = quality failure
2. **Quality Score Rule**: Score below threshold = quality failure
3. **High Issue Rule**: Too many high issues = quality failure
4. **File Concentration Rule**: Too many issues in one file = quality failure
5. **Percentage Rule**: Too high percentage of severe issues = quality failure

### Technical Rules
1. **Score Range**: Quality scores must be 0-100
2. **Status Consistency**: Quality status must align with quality gates
3. **Threshold Validation**: All thresholds must be reasonable values
4. **Issue Classification**: All issues must have valid severity levels

## Migration Strategy

### Data Model Migration
1. **Backward Compatibility**: Existing ValidationResult instances remain valid
2. **Default Values**: New fields have sensible defaults
3. **Status Mapping**: Legacy status values mapped to orchestration_status
4. **Configuration Migration**: Existing configs upgraded with defaults

### Template Migration
1. **Progressive Enhancement**: Templates updated incrementally
2. **Fallback Logic**: Graceful degradation for missing data
3. **Testing**: Comprehensive template testing with new data structure
4. **Documentation**: Updated template documentation and examples