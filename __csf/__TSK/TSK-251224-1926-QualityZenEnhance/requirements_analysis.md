# Requirements Analysis: Enhance /quality System with zen* and llm* Capabilities

**Project**: TSK-251224-1926-QualityZenEnhance
**Date**: 2024-12-24
**Status**: Requirements Analysis Complete
**Version**: 1.0.0

## Executive Summary

This requirements analysis document details the functional, technical, data, integration, and non-functional requirements for enhancing the `/quality` (qual-gate) system to fully leverage updated zen* and llm* capabilities. The enhancement will expand review coverage from 3 to 12 categories, add universal verification, integrate actionability classification, implement cost optimization, enable code compression, and expose consensus quality metrics.

### Key Metrics
- **Current Focus Areas**: 3 (design, clarity, reasoning)
- **Target Focus Areas**: 12 (security, bugs, error_handling, configuration, performance, concurrency, code_quality, testing, api_design, type_safety, dependencies, documentation)
- **Target Cost Reduction**: 50%+
- **Target Token Savings**: 89% for large projects
- **Target False Positive Reduction**: >80%

---

## 1. Functional Requirements Breakdown

### FR1: Focus Area Expansion (3 → 12 Categories)

#### FR1.1: Category Mapping System
**Description**: Map legacy focus areas to new 12-category system

| Legacy Area | New Category(s) | Rationale |
|-------------|----------------|-----------|
| design | code_quality, api_design, architecture | Split into specific aspects |
| clarity | code_quality, documentation | Code clarity vs doc clarity |
| reasoning | bugs, error_handling | Logic issues vs error handling |

**Acceptance Criteria**:
- [ ] Legacy configs using 'design' map to ['code_quality', 'api_design']
- [ ] Legacy configs using 'clarity' map to ['code_quality', 'documentation']
- [ ] Legacy configs using 'reasoning' map to ['bugs', 'error_handling']
- [ ] Mapping is transparent to user (logged but backward compatible)
- [ ] New configs can use any of 12 categories directly
- [ ] Test: Legacy config produces equivalent results

**Implementation Priority**: High (Required for backward compatibility)

#### FR1.2: Default Focus Area Configuration
**Description**: Update default focus areas to align with zen mid-mode

**Current Default**:
```python
default_focus = ['design', 'clarity', 'reasoning']
```

**New Default**:
```python
default_focus = ['security', 'bugs', 'error_handling', 'configuration', 'performance']
```

**Acceptance Criteria**:
- [ ] New defaults match zen mid-mode categories
- [ ] Defaults can be overridden via CLI, config file, or env var
- [ ] Priority: CLI > config file > env var > defaults
- [ ] Test: Fresh install uses new defaults
- [ ] Test: Existing configs with legacy areas still work

**Implementation Priority**: High (Affects default behavior)

#### FR1.3: Category Validation
**Description**: Validate focus areas against available categories

**Valid Categories**:
```python
VALID_CATEGORIES = [
    'security', 'bugs', 'error_handling', 'configuration',
    'performance', 'concurrency', 'code_quality', 'testing',
    'api_design', 'type_safety', 'dependencies', 'documentation'
]
```

**Acceptance Criteria**:
- [ ] Invalid category names rejected with clear error message
- [ ] Error message lists valid categories
- [ ] Partial matches allowed (e.g., 'sec' → 'security') with confirmation
- [ ] Test: Invalid category raises ValueError with helpful message
- [ ] Test: Valid categories pass validation
- [ ] Test: Case-insensitive matching

**Implementation Priority**: Medium (UX improvement)

---

### FR2: Universal Verification System

#### FR2.1: Verification Configuration
**Description**: Enable finding verification for all review types

**Configuration Schema**:
```json
{
  "gates": {
    "code_review": {
      "verify_findings": true,
      "verify_threshold": 0.7
    },
    "final_check": {
      "verify_findings": true,
      "verify_threshold": 0.8
    }
  }
}
```

**Acceptance Criteria**:
- [ ] Verification configurable per-gate
- [ ] Default: verify_findings = False (opt-in for backward compatibility)
- [ ] CLI flag: --verify to enable for all gates
- [ ] CLI flag: --no-verify to explicitly disable
- [ ] Test: Verification enabled filters >80% false positives
- [ ] Test: Verification disabled includes all findings
- [ ] Test: Config file overrides CLI defaults

**Implementation Priority**: High (Quality improvement)

#### FR2.2: Verification Integration
**Description**: Integrate FindingVerifier into zen adapter

**Integration Points**:
1. **ZenCodeReviewAdapter.review_target()**
   - Add `verify: bool` parameter (already exists)
   - Apply verification after consensus aggregation
   - Return verification statistics in result

2. **EnhancedQualityExecutor**
   - Pass verification flag from config to zen adapter
   - Log verification statistics

**Acceptance Criteria**:
- [ ] FindingVerifier imported and instantiated correctly
- [ ] Verification applied to consensus_findings (not raw findings)
- [ ] Verification stats included in result: {verified, false_positives, total}
- [ ] Test: Verified findings have actual_code field populated
- [ ] Test: False positives filtered from consensus_findings
- [ ] Test: Verification completes in <30 seconds for typical projects

**Implementation Priority**: High (Core feature)

#### FR2.3: Verification Reporting
**Description**: Display verification results in quality reports

**Report Format**:
```
🔍 Verification Results
  Total Findings: 50
  Verified: 42 (84%)
  False Positives Filtered: 8 (16%)
  Verification Time: 12.3s
```

**Acceptance Criteria**:
- [ ] Verification stats shown in zen review output
- [ ] Stats included in JSON output
- [ ] Test: Report shows correct counts
- [ ] Test: Markdown report includes verification section
- [ ] Test: JSON includes verification object with stats

**Implementation Priority**: Medium (Reporting feature)

---

### FR3: Actionability Classification Integration

#### FR3.1: Classification Integration
**Description**: Integrate ActionabilityClassifier into zen adapter

**Integration Points**:
1. **ZenCodeReviewAdapter**
   - Import ActionabilityClassifier
   - Classify findings after verification
   - Add classification metadata to findings

2. **Finding Schema Enhancement**:
```python
{
    "category": "security",
    "severity": "high",
    "description": "Missing input validation",
    "file": "api.py",
    "line": 42,
    "verified": true,
    "actionability": {
        "owner": "claude",  # or "user", "hybrid"
        "autonomous": true,
        "needs_user_input": false,
        "complexity": "low",
        "estimated_time": "2 minutes",
        "confidence": 0.95
    }
}
```

**Acceptance Criteria**:
- [ ] ActionabilityClassifier imported and instantiated
- [ ] All findings classified after verification
- [ ] Classification added to finding metadata
- [ ] Test: Autonomous findings marked correctly
- [ ] Test: User decision findings marked correctly
- [ ] Test: Classification confidence >0.7 for 90% of findings

**Implementation Priority**: High (Workflow optimization)

#### FR3.2: Actionability Metrics
**Description**: Track and display actionability metrics

**Metrics Schema**:
```json
{
  "actionability_summary": {
    "total_findings": 50,
    "autonomous": 15,
    "user_decision": 30,
    "hybrid": 5,
    "autonomous_percentage": 30,
    "complexity_breakdown": {
      "low": 20,
      "medium": 25,
      "high": 5
    }
  }
}
```

**Acceptance Criteria**:
- [ ] Actionability summary calculated for each review
- [ ] Metrics displayed in quality report
- [ ] Metrics included in JSON output
- [ ] Test: Autonomous count matches autonomous findings
- [ ] Test: Complexity breakdown accurate
- [ ] Test: Target >30% autonomous findings achieved

**Implementation Priority**: Medium (Metrics feature)

#### FR3.3: CLI Flags for Classification
**Description**: Add CLI flags for actionability classification

**CLI Flags**:
```bash
--classify       # Enable classification (default)
--no-classify    # Disable classification
--autonomous-only # Show only autonomous findings
```

**Acceptance Criteria**:
- [ ] --classify flag enables classification
- [ ] --no-classify flag disables classification
- [ ] Default: classification enabled
- [ ] Test: --no-classify omits actionability field
- [ ] Test: --autonomous-only filters findings

**Implementation Priority**: Low (UX improvement)

---

### FR4: Cost Optimization with Free Providers

#### FR4.1: Cost Strategy Configuration
**Description**: Implement provider selection strategies

**Strategy Definitions**:
```python
COST_STRATEGIES = {
    'aggressive': {
        'free_threshold': 1.0,  # 100% free providers
        'description': 'Use only free providers (OpenRouter free models, Groq)'
    },
    'balanced': {
        'free_threshold': 0.7,  # 70% free, 30% paid
        'description': 'Mix of free and paid providers for quality'
    },
    'quality_first': {
        'free_threshold': 0.5,  # 50% free, 50% paid (best models)
        'description': 'Prioritize quality over cost'
    }
}
```

**Acceptance Criteria**:
- [ ] Three strategies implemented: aggressive, balanced, quality_first
- [ ] Default strategy: balanced
- [ ] CLI flag: --cost-optimize {aggressive,balanced,quality_first}
- [ ] Config file option: cost_optimization_strategy
- [ ] Test: Aggressive uses only free providers
- [ ] Test: Balanced uses 70% free providers
- [ ] Test: Target 50%+ cost reduction vs baseline

**Implementation Priority**: High (Cost optimization)

#### FR4.2: Provider Priority Integration
**Description**: Integrate with zen provider priority system

**Integration Points**:
1. **APIKeyManager**
   - Filter providers by cost strategy
   - Sort by priority within cost tier
   - Track cost per provider

2. **ZenCodeReviewAdapter**
   - Pass cost strategy to orchestrator
   - Log provider selection and costs

**Acceptance Criteria**:
- [ ] Provider list filtered by cost strategy
- [ ] Free providers prioritized when strategy allows
- [ ] Cost tracking per provider implemented
- [ ] Test: Aggressive strategy selects only free providers
- [ ] Test: Cost savings calculated and logged

**Implementation Priority**: High (Core cost feature)

#### FR4.3: Cost Reporting
**Description**: Display cost optimization metrics

**Report Format**:
```
💰 Cost Optimization
  Strategy: balanced (70% free providers)
  Providers Used: 5
  Free Providers: 3 (60%)
  Paid Providers: 2 (40%)
  Estimated Cost: $0.42
  Cost Savings: $0.38 (48% reduction)
```

**Acceptance Criteria**:
- [ ] Cost summary displayed in review output
- [ ] Cost breakdown by provider shown
- [ ] Savings vs default strategy calculated
- [ ] Test: Cost matches provider pricing
- [ ] Test: Savings percentage accurate

**Implementation Priority**: Medium (Reporting feature)

---

### FR5: Code Compression for Large Projects

#### FR5.1: Compression Configuration
**Description**: Enable AI Distiller code compression

**Configuration Schema**:
```json
{
  "code_compression": {
    "enabled": true,
    "threshold_lines": 10000,
    "target_ratio": 0.11,  # 89% compression
    "compression_method": "ai_distiller"
  }
}
```

**Acceptance Criteria**:
- [ ] Compression configurable via config file
- [ ] Default threshold: 10,000 lines
- [ ] CLI flags: --compress, --compress-threshold N
- [ ] Test: Projects >10k lines auto-compressed
- [ ] Test: Projects <10k lines not compressed
- [ ] Test: Target 89% token savings achieved

**Implementation Priority**: Medium (Performance feature)

#### FR5.2: Compression Integration
**Description**: Integrate AI Distiller for code compression

**Integration Points**:
1. **ZenCodeReviewAdapter**
   - Detect project size before review
   - Call AI Distiller if threshold exceeded
   - Use compressed diff for review

2. **Diff Generator**
   - Add compression step
   - Preserve original file references
   - Log compression statistics

**Acceptance Criteria**:
- [ ] Line count detection accurate
- [ ] Compression triggered when threshold exceeded
- [ ] Compressed diff used for LLM review
- [ ] Original file paths preserved
- [ ] Test: 10k+ line project compressed
- [ ] Test: Compression completes in <5 seconds overhead

**Implementation Priority**: Medium (Large project support)

#### FR5.3: Compression Reporting
**Description**: Display compression statistics

**Report Format**:
```
🗜️ Code Compression
  Project Size: 15,432 lines
  Threshold: 10,000 lines
  Compressed: Yes
  Original Tokens: 45,000
  Compressed Tokens: 5,000
  Compression Ratio: 89%
  Compression Time: 3.2s
```

**Acceptance Criteria**:
- [ ] Compression stats displayed in review output
- [ ] Token savings calculated
- [ ] Compression time logged
- [ ] Test: Stats accurate for compressed projects
- [ ] Test: No stats for uncompressed projects

**Implementation Priority**: Low (Reporting feature)

---

### FR6: Consensus Quality Metrics

#### FR6.1: Consensus Scoring
**Description**: Expose consensus quality scores from orchestrator

**Score Schema**:
```python
{
    "consensus_score": 0.85,  # 0.0 to 1.0
    "agreement_level": "high",  # high, medium, low
    "provider_agreement": {
        "total_providers": 5,
        "agreeing_providers": 4,
        "dissenting_providers": 1
    },
    "confidence": 0.92
}
```

**Acceptance Criteria**:
- [ ] Consensus score calculated for each finding
- [ ] Agreement level determined (high: ≥2 providers, medium: 1, low: dissenting)
- [ ] Provider counts tracked
- [ ] Test: High agreement findings have score ≥0.7
- [ ] Test: Dissenting findings have score ≤0.3
- [ ] Test: >70% high-agreement findings in chad mode

**Implementation Priority**: High (Quality signal)

#### FR6.2: Consensus Display
**Description**: Display consensus metrics in quality reports

**Report Format**:
```
📊 Consensus Quality
  Total Findings: 50
  High Agreement (≥2 providers): 35 (70%)
  Medium Agreement (1 provider): 12 (24%)
  Low Agreement (Dissenting): 3 (6%)
  Consensus Score: 0.78
```

**Acceptance Criteria**:
- [ ] Consensus breakdown displayed in report
- [ ] Agreement levels color-coded (high: green, medium: yellow, low: red)
- [ ] Consensus score prominently displayed
- [ ] Test: Report matches finding counts
- [ ] Test: Score calculation accurate

**Implementation Priority**: Medium (Reporting feature)

#### FR6.3: Consensus Filtering
**Description**: Allow filtering by consensus level

**CLI Flags**:
```bash
--consensus-high     # Show only high-agreement findings
--consensus-minimum 0.7  # Minimum consensus score threshold
```

**Acceptance Criteria**:
- [ ] --consensus-high filters to high-agreement findings
- [ ] --consensus-minimum filters by score threshold
- [ ] Filter criteria logged in output
- [ ] Test: High filter shows only findings with ≥2 providers
- [ ] Test: Score threshold filter accurate

**Implementation Priority**: Low (UX improvement)

---

## 2. Technical Requirements

### TR1: Python Version Compatibility
**Requirement**: Support Python 3.10+ (CSF NIP standard)

**Specification**:
```python
# pyproject.toml
requires-python = ">=3.10"
```

**Acceptance Criteria**:
- [ ] Code tested on Python 3.10, 3.11, 3.12
- [ ] No use of Python 3.13+ features
- [ ] Type hints compatible with 3.10
- [ ] Test: All tests pass on 3.10

**Implementation Priority**: High (Compatibility)

---

### TR2: Dependencies
**Requirement**: Define and manage dependencies

**Core Dependencies**:
```python
# Existing
from quality.zen_review_adapter import ZenCodeReviewAdapter
from quality.enhanced_execution import EnhancedQualityExecutor

# New dependencies
from zen.lib.finding_verifier import FindingVerifier
from zen.lib.actionability_classifier import ActionabilityClassifier
from zen_integration.provider_wrapper import ProviderWrapper
from zen_integration.api_key_manager import APIKeyManager
```

**Acceptance Criteria**:
- [ ] All dependencies version-pinned
- [ ] Dependency documentation updated
- [ ] Optional dependencies clearly marked
- [ ] Test: All imports work without errors

**Implementation Priority**: High (Functionality)

---

### TR3: API Interfaces
**Requirement**: Define clear API interfaces

#### TR3.1: ZenCodeReviewAdapter Interface
```python
class ZenCodeReviewAdapter:
    def review_target(
        self,
        target: str,
        mode: str = "mid",
        focus_areas: Optional[List[str]] = None,
        context: Optional[str] = None,
        verify: bool = False,  # FR2
        classify: bool = True,  # FR3
        cost_strategy: str = "balanced",  # FR4
        compress: bool = False,  # FR5
        compress_threshold: int = 10000  # FR5
    ) -> Dict[str, Any]:
        """Run LLM code review with all enhancements."""
        pass
```

**Acceptance Criteria**:
- [ ] Interface defined in adapter
- [ ] Type hints complete
- [ ] Docstring comprehensive
- [ ] Test: All parameters work correctly

**Implementation Priority**: High (API design)

#### TR3.2: EnhancedQualityExecutor Interface
```python
class EnhancedQualityExecutor:
    def __init__(
        self,
        working_dir: str,
        review_mode: str = None,
        focus_areas: list = None,
        verify_findings: bool = False,  # FR2
        classify_findings: bool = True,  # FR3
        cost_strategy: str = "balanced",  # FR4
        compress_code: bool = False  # FR5
    ):
        """Initialize enhanced executor with all features."""
        pass
```

**Acceptance Criteria**:
- [ ] Constructor accepts all enhancement parameters
- [ ] Parameters passed to zen adapter correctly
- [ ] Test: Executor initializes with all options

**Implementation Priority**: High (API design)

---

### TR4: Configuration Schema
**Requirement**: Define comprehensive configuration schema

**Complete Schema**:
```json
{
  "$schema": "./qual-gate-schema-v1.json",
  "version": "1.0",
  "gates": {
    "code_review": {
      "enabled": true,
      "review_mode": "mid",
      "focus_areas": [
        "security", "bugs", "error_handling",
        "configuration", "performance"
      ],
      "verify_findings": false,
      "classify_findings": true,
      "cost_optimization_strategy": "balanced",
      "code_compression": {
        "enabled": false,
        "threshold_lines": 10000
      }
    },
    "final_check": {
      "enabled": true,
      "review_mode": "mid",
      "focus_areas": ["security", "performance"],
      "verify_findings": true,
      "classify_findings": true,
      "cost_optimization_strategy": "quality_first",
      "code_compression": {
        "enabled": true,
        "threshold_lines": 10000
      }
    }
  },
  "category_mapping": {
    "design": ["code_quality", "api_design"],
    "clarity": ["code_quality", "documentation"],
    "reasoning": ["bugs", "error_handling"]
  }
}
```

**Acceptance Criteria**:
- [ ] Schema validates all config options
- [ ] Schema documented
- [ ] Default config file created on init
- [ ] Test: Valid config loads successfully
- [ ] Test: Invalid config fails with clear error

**Implementation Priority**: High (Configuration)

---

## 3. Data Requirements

### DR1: Input/Output Formats

#### DR1.1: Review Request Format
```python
{
    "target": "/path/to/repo",
    "mode": "mid",  # chill, mid, chad
    "focus_areas": ["security", "bugs", "error_handling"],
    "context": "PR #123: Add user authentication",
    "verify": true,
    "classify": true,
    "cost_strategy": "balanced",
    "compress": false
}
```

**Acceptance Criteria**:
- [ ] Request format documented
- [ ] JSON validation implemented
- [ ] Test: Valid request accepted
- [ ] Test: Invalid request rejected

**Implementation Priority**: Medium (Documentation)

#### DR1.2: Review Response Format
```python
{
    "success": true,
    "metadata": {
        "mode": "mid",
        "focus_areas": ["security", "bugs"],
        "providers_used": ["claude", "gpt4", "gemini"],
        "review_duration_seconds": 45.2
    },
    "consensus_findings": [
        {
            "id": "finding_001",
            "category": "security",
            "severity": "high",
            "description": "Missing input validation",
            "file": "api.py",
            "line": 42,
            "code_snippet": "def login(username):",
            "verified": true,
            "consensus": {
                "score": 0.92,
                "level": "high",
                "agreeing_providers": 5,
                "total_providers": 5
            },
            "actionability": {
                "owner": "claude",
                "autonomous": true,
                "complexity": "low",
                "estimated_time": "2 minutes",
                "confidence": 0.95
            }
        }
    ],
    "verification": {
        "total": 50,
        "verified": 42,
        "false_positives": 8,
        "duration_seconds": 12.3
    },
    "actionability_summary": {
        "total": 42,
        "autonomous": 15,
        "user_decision": 25,
        "hybrid": 2
    },
    "consensus_summary": {
        "total": 42,
        "high_agreement": 30,
        "medium_agreement": 10,
        "low_agreement": 2,
        "overall_score": 0.78
    },
    "cost_summary": {
        "strategy": "balanced",
        "estimated_cost_usd": 0.42,
        "savings_usd": 0.38,
        "savings_percentage": 48
    },
    "compression": {
        "enabled": false,
        "original_tokens": 0,
        "compressed_tokens": 0
    }
}
```

**Acceptance Criteria**:
- [ ] Response format documented
- [ ] All fields present when enabled
- [ ] Optional fields omitted when disabled
- [ ] Test: Response matches schema
- [ ] Test: JSON serializable

**Implementation Priority**: High (API contract)

---

### DR2: Configuration Data Structures

#### DR2.1: Category Mapping Structure
```python
CATEGORY_MAPPING = {
    # Legacy → New mappings
    "design": ["code_quality", "api_design"],
    "clarity": ["code_quality", "documentation"],
    "reasoning": ["bugs", "error_handling"],

    # Direct mappings (no change)
    "security": ["security"],
    "performance": ["performance"],
    "bugs": ["bugs"],
    "style": ["code_quality"]
}
```

**Acceptance Criteria**:
- [ ] Mapping structure defined
- [ ] Mapping function implemented
- [ ] Test: Legacy areas map correctly
- [ ] Test: New areas pass through

**Implementation Priority**: High (Backward compatibility)

#### DR2.2: Cost Strategy Structure
```python
COST_STRATEGIES = {
    "aggressive": {
        "free_threshold": 1.0,
        "providers": ["openrouter_free", "groq"],
        "description": "100% free providers"
    },
    "balanced": {
        "free_threshold": 0.7,
        "providers": ["openrouter_free", "groq", "claude"],
        "description": "70% free, 30% paid"
    },
    "quality_first": {
        "free_threshold": 0.5,
        "providers": ["claude", "gpt4", "gemini"],
        "description": "50% free, 50% paid (best quality)"
    }
}
```

**Acceptance Criteria**:
- [ ] Strategy structure defined
- [ ] Provider selection logic implemented
- [ ] Test: Aggressive uses only free
- [ ] Test: Balanced mixes providers
- [ ] Test: Quality_first prioritizes quality

**Implementation Priority**: High (Cost optimization)

---

### DR3: Review Findings Schema
**Requirement**: Define comprehensive finding schema

**Complete Finding Schema**:
```python
@dataclass
class ReviewFinding:
    """Complete review finding with all enhancements."""

    # Core fields
    id: str
    category: str
    severity: str  # critical, high, medium, low, info
    description: str

    # Location
    file: str
    line: int
    column: Optional[int]
    code_snippet: str
    context_lines: List[str]

    # Verification (FR2)
    verified: bool
    confidence: float  # 0.0 to 1.0
    actual_code: str
    false_positive_reason: Optional[str]

    # Consensus (FR6)
    consensus_score: float
    agreement_level: str  # high, medium, low
    agreeing_providers: int
    total_providers: int

    # Actionability (FR3)
    autonomous: bool
    needs_user_input: bool
    owner: str  # claude, user, hybrid
    implementation_complexity: str  # low, medium, high
    estimated_time: str
    actionability_confidence: float
    prerequisites: List[str]

    # Suggestion (optional)
    suggested_fix: Optional[str]
    example_code: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        pass
```

**Acceptance Criteria**:
- [ ] Finding dataclass defined
- [ ] All fields typed
- [ ] to_dict() method implemented
- [ ] Test: Finding serializes to JSON
- [ ] Test: All fields present in output

**Implementation Priority**: High (Data model)

---

### DR4: Consensus Metrics Format
**Requirement**: Define consensus metrics structure

**Consensus Metrics Schema**:
```python
@dataclass
class ConsensusMetrics:
    """Consensus quality metrics for a review."""

    total_findings: int
    high_agreement_count: int  # ≥2 providers
    medium_agreement_count: int  # 1 provider
    low_agreement_count: int  # Dissenting

    overall_score: float  # Weighted average
    confidence: float  # Statistical confidence

    provider_breakdown: Dict[str, int]  # provider → agreement count

    def calculate_agreement_percentage(self) -> Dict[str, float]:
        """Calculate percentage for each agreement level."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        pass
```

**Acceptance Criteria**:
- [ ] Metrics dataclass defined
- [ ] Calculation methods implemented
- [ ] Test: Scores calculated correctly
- [ ] Test: Percentages accurate

**Implementation Priority**: High (Metrics)

---

## 4. Integration Requirements

### IR1: ZenCodeReviewAdapter Enhancements

#### IR1.1: Add Verification Support
**Location**: `P:/__csf.nip/src/quality/zen_review_adapter.py`

**Changes Required**:
```python
# In review_target method:
def review_target(
    self,
    target: str,
    mode: str = "mid",
    focus_areas: Optional[List[str]] = None,
    context: Optional[str] = None,
    verify: bool = False,  # Already exists, enhance
    classify: bool = True,  # NEW
    cost_strategy: str = "balanced",  # NEW
    compress: bool = False,  # NEW
    compress_threshold: int = 10000  # NEW
) -> Dict[str, Any]:
    """Run LLM code review with all enhancements."""

    # ... existing code ...

    # Apply verification if requested (already exists)
    if verify:
        findings_to_verify = result.get('consensus_findings', [])

        if findings_to_verify:
            from zen.lib.finding_verifier import FindingVerifier

            verifier = FindingVerifier(root_path=Path(target).resolve())
            verified_findings, verification_stats = verifier.verify_batch(findings_to_verify)

            result['consensus_findings'] = verified_findings
            result['verification'] = verification_stats
            result['verified'] = True

    # NEW: Apply actionability classification
    if classify and result.get('consensus_findings'):
        from zen.lib.actionability_classifier import ActionabilityClassifier

        classifier = ActionabilityClassifier()
        classified_findings = []
        actionability_summary = {
            'total': 0,
            'autonomous': 0,
            'user_decision': 0,
            'hybrid': 0
        }

        for finding in result['consensus_findings']:
            classification = classifier.classify(
                finding,
                verified_code=finding.get('actual_code', '')
            )

            finding['actionability'] = classification.to_dict()
            classified_findings.append(finding)

            # Update summary
            actionability_summary['total'] += 1
            if classification.autonomous:
                actionability_summary['autonomous'] += 1
            elif classification.needs_user_input:
                actionability_summary['user_decision'] += 1
            else:
                actionability_summary['hybrid'] += 1

        result['consensus_findings'] = classified_findings
        result['actionability_summary'] = actionability_summary

    # NEW: Apply cost strategy
    # (Pass cost_strategy to orchestrator for provider selection)

    # NEW: Apply code compression
    # (Check project size, compress if needed)

    return result
```

**Acceptance Criteria**:
- [ ] FindingVerifier integrated
- [ ] ActionabilityClassifier integrated
- [ ] Verification stats returned
- [ ] Actionability summary returned
- [ ] Test: Full workflow with all enhancements

**Implementation Priority**: High (Core integration)

---

### IR2: EnhancedQualityExecutor Modifications

#### IR2.1: Pass Enhancement Parameters
**Location**: `P:/__csf.nip/src/quality/enhanced_execution.py`

**Changes Required**:
```python
class EnhancedQualityExecutor:
    def __init__(
        self,
        working_dir: str,
        review_mode: str = None,
        focus_areas: list = None,
        verify_findings: bool = False,  # NEW
        classify_findings: bool = True,  # NEW
        cost_strategy: str = "balanced",  # NEW
        compress_code: bool = False  # NEW
    ):
        """Initialize enhanced executor with all features."""
        self.working_dir = Path(working_dir).resolve()
        self.discover_adapter = DiscoverAdapter()
        self.zen_adapter = ZenCodeReviewAdapter()

        # Load configuration with hybrid priority
        self.review_mode, self.focus_areas = self._load_review_config(
            cli_mode=review_mode,
            cli_focus=focus_areas
        )

        # NEW: Load enhancement configs
        self.verify_findings = self._load_enhancement_config(
            'verify_findings',
            cli_value=verify_findings,
            default=False
        )
        self.classify_findings = self._load_enhancement_config(
            'classify_findings',
            cli_value=classify_findings,
            default=True
        )
        self.cost_strategy = self._load_enhancement_config(
            'cost_optimization_strategy',
            cli_value=cost_strategy,
            default='balanced'
        )
        self.compress_code = self._load_enhancement_config(
            'code_compression.enabled',
            cli_value=compress_code,
            default=False
        )

    def _load_enhancement_config(
        self,
        config_key: str,
        cli_value: Any = None,
        default: Any = None
    ) -> Any:
        """Load enhancement config with hybrid priority."""
        # Priority: CLI > config file > env var > default
        if cli_value is not None:
            return cli_value

        # Check config file (support nested keys like "code_compression.enabled")
        config = self._load_config_file()
        keys = config_key.split('.')
        value = config
        for key in keys:
            value = value.get(key, {})
            if not isinstance(value, dict):
                break

        if value and not isinstance(value, dict):
            return value

        # Check environment variable
        env_key = f"QUAL_GATE_{config_key.replace('.', '_').upper()}"
        env_value = os.environ.get(env_key)
        if env_value is not None:
            # Convert string to appropriate type
            if isinstance(default, bool):
                return env_value.lower() in ('true', '1', 'yes')
            elif isinstance(default, int):
                return int(env_value)
            return env_value

        return default

    def execute_cognitive_review_phase(self) -> Dict[str, Any]:
        """Execute cognitive review phase with all enhancements."""
        print("🧠 Enhanced Cognitive Review Phase with Multi-LLM Analysis")

        results = {
            'phase': 'cognitive_review',
            'zen_review': None,
            'tool_status': {}
        }

        if self.zen_available:
            print("  → Running multi-LLM semantic review...")

            # Pass all enhancement parameters
            review = self.zen_adapter.review_target(
                target=str(self.working_dir),
                mode=self.review_mode,
                focus_areas=self.focus_areas,
                verify=self.verify_findings,  # NEW
                classify=self.classify_findings,  # NEW
                cost_strategy=self.cost_strategy,  # NEW
                compress=self.compress_code  # NEW
            )

            if review.get('success'):
                print("  ✓ Multi-LLM review completed")

                # NEW: Display verification results
                if review.get('verified'):
                    verification_stats = review.get('verification', {})
                    total = verification_stats.get('total', 0)
                    verified = verification_stats.get('verified', 0)
                    false_positives = verification_stats.get('false_positives', 0)
                    print(f"    🔍 Verification: {verified}/{total} findings verified, {false_positives} filtered")

                # NEW: Display actionability summary
                if review.get('actionability_summary'):
                    actionability = review['actionability_summary']
                    autonomous_pct = (actionability['autonomous'] / actionability['total'] * 100) if actionability['total'] > 0 else 0
                    print(f"    🤖 Autonomous: {actionability['autonomous']}/{actionability['total']} ({autonomous_pct:.0f}%)")

                # NEW: Display consensus summary
                if review.get('consensus_summary'):
                    consensus = review['consensus_summary']
                    high_pct = (consensus['high_agreement'] / consensus['total'] * 100) if consensus['total'] > 0 else 0
                    print(f"    📊 High Agreement: {consensus['high_agreement']}/{consensus['total']} ({high_pct:.0f}%)")

                # NEW: Display cost summary
                if review.get('cost_summary'):
                    cost = review['cost_summary']
                    print(f"    💰 Cost: ${cost['estimated_cost_usd']:.2f} (saved {cost['savings_percentage']:.0f}%)")

                results['zen_review'] = review
                results['tool_status']['zen_cognitive_review'] = 'completed'

        return results
```

**Acceptance Criteria**:
- [ ] Enhancement parameters loaded correctly
- [ ] Parameters passed to zen adapter
- [ ] Enhancement results displayed
- [ ] Test: All enhancements work together

**Implementation Priority**: High (Core integration)

---

### IR3: qual-gate.py CLI Additions

#### IR3.1: Add Enhancement CLI Flags
**Location**: `P:/__csf.nip/src/quality/qual-gate.py`

**CLI Argument Additions**:
```python
# In argument parser setup:
parser.add_argument(
    '--verify',
    action='store_true',
    help='Enable finding verification (filter false positives)'
)
parser.add_argument(
    '--no-verify',
    action='store_true',
    help='Disable finding verification'
)
parser.add_argument(
    '--classify',
    action='store_true',
    default=True,
    help='Enable actionability classification (default: enabled)'
)
parser.add_argument(
    '--no-classify',
    action='store_true',
    help='Disable actionability classification'
)
parser.add_argument(
    '--cost-optimize',
    choices=['aggressive', 'balanced', 'quality_first'],
    default='balanced',
    help='Cost optimization strategy (default: balanced)'
)
parser.add_argument(
    '--compress',
    action='store_true',
    help='Enable code compression for large projects'
)
parser.add_argument(
    '--compress-threshold',
    type=int,
    default=10000,
    help='Code compression threshold in lines (default: 10000)'
)
parser.add_argument(
    '--focus',
    nargs='+',
    choices=[
        'security', 'bugs', 'error_handling', 'configuration',
        'performance', 'concurrency', 'code_quality', 'testing',
        'api_design', 'type_safety', 'dependencies', 'documentation'
    ],
    help='Focus areas for code review (12 categories available)'
)
```

**Acceptance Criteria**:
- [ ] All CLI flags added
- [ ] Flag defaults correct
- [ ] Help text comprehensive
- [ ] Test: Flags control behavior correctly

**Implementation Priority**: High (CLI interface)

#### IR3.2: Pass CLI Arguments to Executor
**Changes Required**:
```python
# In main execution:
executor = EnhancedQualityExecutor(
    working_dir=args.working_dir,
    review_mode=args.review_mode,
    focus_areas=args.focus,
    verify_findings=args.verify,  # NEW
    classify_findings=not args.no_classify,  # NEW
    cost_strategy=args.cost_optimize,  # NEW
    compress_code=args.compress  # NEW
)
```

**Acceptance Criteria**:
- [ ] All CLI arguments passed to executor
- [ ] Boolean flags handled correctly
- [ ] Test: CLI flags work as expected

**Implementation Priority**: High (CLI integration)

---

### IR4: Configuration File Schema

#### IR4.1: Create Default Config Template
**Location**: `P:/__csf.nip/.qual-gate.json.template`

**Template Content**:
```json
{
  "$schema": "./qual-gate-schema-v1.json",
  "version": "1.0",
  "gates": {
    "code_review": {
      "enabled": true,
      "review_mode": "mid",
      "focus_areas": [
        "security",
        "bugs",
        "error_handling",
        "configuration",
        "performance"
      ],
      "verify_findings": false,
      "classify_findings": true,
      "cost_optimization_strategy": "balanced",
      "code_compression": {
        "enabled": false,
        "threshold_lines": 10000
      }
    },
    "final_check": {
      "enabled": true,
      "review_mode": "mid",
      "focus_areas": [
        "security",
        "performance",
        "bugs"
      ],
      "verify_findings": true,
      "classify_findings": true,
      "cost_optimization_strategy": "quality_first",
      "code_compression": {
        "enabled": true,
        "threshold_lines": 10000
      }
    }
  },
  "category_mapping": {
    "design": ["code_quality", "api_design"],
    "clarity": ["code_quality", "documentation"],
    "reasoning": ["bugs", "error_handling"]
  },
  "cost_strategies": {
    "aggressive": {
      "description": "Use only free providers (maximum cost savings)",
      "free_provider_percentage": 100
    },
    "balanced": {
      "description": "Mix of free and paid providers (recommended)",
      "free_provider_percentage": 70
    },
    "quality_first": {
      "description": "Prioritize best models over cost",
      "free_provider_percentage": 50
    }
  }
}
```

**Acceptance Criteria**:
- [ ] Template file created
- [ ] All configuration options documented
- [ ] Schema reference included
- [ ] Test: Template validates against schema

**Implementation Priority**: Medium (Documentation)

---

## 5. Non-Functional Requirements

### NFR1: Backward Compatibility

#### NFR1.1: Legacy Config Support
**Requirement**: Existing configs work without modification

**Test Cases**:
1. Legacy focus areas (design, clarity, reasoning) map correctly
2. Configs without enhancement fields use defaults
3. CLI behavior unchanged when flags not specified

**Acceptance Criteria**:
- [ ] Legacy configs load without errors
- [ ] Legacy areas produce equivalent results
- [ ] New features opt-in only
- [ ] Test: Existing .qual-gate.json files work unchanged

**Implementation Priority**: High (Critical requirement)

#### NFR1.2: API Stability
**Requirement**: Existing API contracts maintained

**Stable Interfaces**:
```python
# These interfaces must remain unchanged:
ZenCodeReviewAdapter.review_target()
ZenCodeReviewAdapter.quick_review()
ZenCodeReviewAdapter.comprehensive_review()
EnhancedQualityExecutor.execute_phase()
```

**Acceptance Criteria**:
- [ ] Existing method signatures unchanged
- [ ] New parameters optional with defaults
- [ ] Return format backward compatible
- [ ] Test: Existing code using adapter works unchanged

**Implementation Priority**: High (API stability)

---

### NFR2: Performance Targets

#### NFR2.1: Execution Time
**Requirement**: No significant degradation

**Performance Budgets**:
| Operation | Target | Maximum |
|-----------|--------|---------|
| Gate 6 (code_review) | +10% | +30% |
| Finding verification | <30s | 60s |
| Code compression | <5s overhead | 10s |
| Actionability classification | <5s | 10s |

**Acceptance Criteria**:
- [ ] Gate 6 execution time within 30% of baseline
- [ ] Verification completes in <60 seconds
- [ ] Compression overhead <10 seconds
- [ ] Test: Performance benchmarks meet targets

**Implementation Priority**: Medium (Performance)

#### NFR2.2: Memory Usage
**Requirement**: No significant memory increase

**Memory Budget**:
- Base: ~200MB
- With enhancements: ~300MB
- Maximum: ~500MB

**Acceptance Criteria**:
- [ ] Memory usage monitored
- [ ] No memory leaks in enhancement code
- [ ] Test: Memory usage within budget

**Implementation Priority**: Medium (Resource management)

---

### NFR3: Deterministic Gates

#### NFR3.1: Gate Separation
**Requirement**: Gates 1-5 deterministic, Gates 6-8 LLM-enhanced

**Gate Classification**:
- **Deterministic (1-5)**: structure, governance, architecture, security, apis_services
- **LLM-Enhanced (6-8)**: code_review, performance, final_check

**Acceptance Criteria**:
- [ ] Gates 1-5 use no LLM calls
- [ ] Gates 6-8 can use LLM
- [ ] LLM unavailability doesn't break gates 1-5
- [ ] Test: Quality gate runs with LLM unavailable (gates 1-5 pass)

**Implementation Priority**: High (Architecture principle)

---

### NFR4: Configuration Simplicity

#### NFR4.1: Sensible Defaults
**Requirement**: All features work out-of-the-box

**Default Configuration**:
```python
defaults = {
    'review_mode': 'mid',
    'focus_areas': ['security', 'bugs', 'error_handling', 'configuration', 'performance'],
    'verify_findings': False,
    'classify_findings': True,
    'cost_optimization_strategy': 'balanced',
    'code_compression': {'enabled': False, 'threshold_lines': 10000}
}
```

**Acceptance Criteria**:
- [ ] All features work with no config
- [ ] Defaults optimized for common use cases
- [ ] Test: Fresh install works without configuration

**Implementation Priority**: High (Usability)

#### NFR4.2: Clear Documentation
**Requirement**: Comprehensive documentation

**Documentation Requirements**:
1. Configuration file reference
2. CLI flag reference
3. Feature usage examples
4. Migration guide for legacy configs
5. Troubleshooting guide

**Acceptance Criteria**:
- [ ] README updated with enhancements
- [ ] Config file documented
- [ ] Examples provided
- [ ] Migration guide available
- [ ] Test: Documentation is clear and complete

**Implementation Priority**: Medium (Documentation)

---

### NFR5: Security Considerations

#### NFR5.1: API Key Management
**Requirement**: Secure API key handling

**Security Requirements**:
- No API keys in config files
- Use environment variables or zen key manager
- Keys encrypted at rest
- No keys in logs

**Acceptance Criteria**:
- [ ] API keys loaded from secure sources
- [ ] No keys in version control
- [ ] Keys not logged
- [ ] Test: Keys handled securely

**Implementation Priority**: High (Security)

#### NFR5.2: Code Privacy
**Requirement**: Protect sensitive code

**Privacy Requirements**:
- No code sent to external LLMs without user consent
- Option to run local-only reviews
- Clear disclosure of data usage

**Acceptance Criteria**:
- [ ] Privacy policy documented
- [ ] Local-only mode available
- [ ] User consent obtained
- [ ] Test: Privacy options work

**Implementation Priority**: Medium (Privacy)

---

### NFR6: Usability Requirements

#### NFR6.1: Intuitive CLI
**Requirement**: Easy-to-use command-line interface

**CLI Design Principles**:
- Consistent flag naming
- Clear help text
- Helpful error messages
- Progress indicators

**Acceptance Criteria**:
- [ ] Flags follow naming conventions
- [ ] Help text comprehensive
- [ ] Errors actionable
- [ ] Test: CLI is intuitive

**Implementation Priority**: Medium (UX)

#### NFR6.2: Clear Output
**Requirement**: Understandable review results

**Output Design**:
- Structured sections
- Color-coded severity
- Summary metrics
- Actionable recommendations

**Acceptance Criteria**:
- [ ] Output well-formatted
- [ ] Key metrics highlighted
- [ ] Actionable next steps clear
- [ ] Test: Output is clear and actionable

**Implementation Priority**: Medium (UX)

---

## 6. Acceptance Criteria & Test Planning

### AC1: Functional Requirements Tests

#### Test Suite Structure
```
tests/
├── test_focus_area_expansion.py
│   ├── test_category_mapping.py
│   ├── test_default_configuration.py
│   └── test_category_validation.py
├── test_verification_system.py
│   ├── test_verification_configuration.py
│   ├── test_finding_verifier_integration.py
│   └── test_verification_reporting.py
├── test_actionability_classification.py
│   ├── test_classifier_integration.py
│   ├── test_actionability_metrics.py
│   └── test_classification_cli_flags.py
├── test_cost_optimization.py
│   ├── test_cost_strategies.py
│   ├── test_provider_selection.py
│   └── test_cost_reporting.py
├── test_code_compression.py
│   ├── test_compression_configuration.py
│   ├── test_compression_integration.py
│   └── test_compression_reporting.py
└── test_consensus_metrics.py
    ├── test_consensus_scoring.py
    ├── test_consensus_display.py
    └── test_consensus_filtering.py
```

---

### AC2: Test Cases by Requirement

#### FR1: Focus Area Expansion Tests

**TC-FR1.1: Category Mapping**
```python
def test_legacy_design_maps_to_code_quality_and_api_design():
    """Legacy 'design' focus area maps correctly."""
    config = {'focus_areas': ['design']}
    mapped = map_legacy_focus_areas(config['focus_areas'])
    assert set(mapped) == {'code_quality', 'api_design'}

def test_legacy_clarity_maps_to_code_quality_and_documentation():
    """Legacy 'clarity' focus area maps correctly."""
    config = {'focus_areas': ['clarity']}
    mapped = map_legacy_focus_areas(config['focus_areas'])
    assert set(mapped) == {'code_quality', 'documentation'}

def test_new_categories_pass_through():
    """New 12 categories work directly."""
    config = {'focus_areas': ['security', 'bugs', 'error_handling']}
    mapped = map_legacy_focus_areas(config['focus_areas'])
    assert set(mapped) == {'security', 'bugs', 'error_handling'}
```

**TC-FR1.2: Default Configuration**
```python
def test_default_focus_areas_match_mid_mode():
    """Default focus areas match zen mid-mode."""
    executor = EnhancedQualityExecutor('/tmp/test')
    assert executor.focus_areas == [
        'security', 'bugs', 'error_handling',
        'configuration', 'performance'
    ]

def test_config_file_overrides_defaults():
    """Config file focus areas override defaults."""
    # Create test config
    config = {'focus_areas': ['security', 'performance']}
    executor = EnhancedQualityExecutor('/tmp/test')
    # Config should override
    assert set(executor.focus_areas) == {'security', 'performance'}
```

**TC-FR1.3: Category Validation**
```python
def test_invalid_category_raises_error():
    """Invalid category name raises ValueError."""
    with pytest.raises(ValueError, match="Invalid focus area"):
        validate_focus_areas(['invalid_category'])

def test_valid_categories_pass():
    """Valid categories pass validation."""
    categories = ['security', 'bugs', 'error_handling']
    result = validate_focus_areas(categories)
    assert result == categories

def test_case_insensitive_matching():
    """Category matching is case-insensitive."""
    result = validate_focus_areas(['Security', 'BUGS'])
    assert result == ['security', 'bugs']
```

---

#### FR2: Universal Verification Tests

**TC-FR2.1: Verification Configuration**
```python
def test_verification_disabled_by_default():
    """Verification is opt-in (disabled by default)."""
    executor = EnhancedQualityExecutor('/tmp/test')
    assert executor.verify_findings == False

def test_cli_verify_flag_enables_verification():
    """CLI --verify flag enables verification."""
    executor = EnhancedQualityExecutor(
        '/tmp/test',
        verify_findings=True
    )
    assert executor.verify_findings == True

def test_config_file_overrides_cli():
    """Config file verification setting overrides CLI."""
    # Test priority: CLI > config > env > default
    pass
```

**TC-FR2.2: Verification Integration**
```python
def test_finding_verifier_filters_false_positives():
    """FindingVerifier filters false positives correctly."""
    adapter = ZenCodeReviewAdapter()
    result = adapter.review_target(
        '/tmp/test',
        verify=True
    )
    assert result['verified'] == True
    assert 'verification' in result
    assert result['verification']['false_positives'] >= 0

def test_verification_stats_included_in_result():
    """Verification statistics included in result."""
    adapter = ZenCodeReviewAdapter()
    result = adapter.review_target(
        '/tmp/test',
        verify=True
    )
    stats = result['verification']
    assert 'total' in stats
    assert 'verified' in stats
    assert 'false_positives' in stats
```

**TC-FR2.3: Verification Reporting**
```python
def test_verification_stats_displayed_in_report():
    """Verification stats shown in quality report."""
    # Test report generation
    pass

def test_json_output_includes_verification():
    """JSON output includes verification object."""
    result = adapter.review_target('/tmp/test', verify=True)
    json_output = json.dumps(result)
    assert 'verification' in json_output
```

---

#### FR3: Actionability Classification Tests

**TC-FR3.1: Classification Integration**
```python
def test_actionability_classifier_integration():
    """ActionabilityClassifier integrated into adapter."""
    adapter = ZenCodeReviewAdapter()
    result = adapter.review_target(
        '/tmp/test',
        classify=True
    )

    # Check findings have actionability
    findings = result['consensus_findings']
    for finding in findings:
        assert 'actionability' in finding
        assert 'owner' in finding['actionability']
        assert 'autonomous' in finding['actionability']

def test_classification_confidence_high():
    """Classification confidence >0.7 for 90% of findings."""
    result = adapter.review_target('/tmp/test', classify=True)
    findings = result['consensus_findings']

    high_confidence = [
        f for f in findings
        if f['actionability']['confidence'] > 0.7
    ]

    confidence_pct = len(high_confidence) / len(findings)
    assert confidence_pct >= 0.9
```

**TC-FR3.2: Actionability Metrics**
```python
def test_actionability_summary_calculated():
    """Actionability summary calculated correctly."""
    result = adapter.review_target('/tmp/test', classify=True)
    summary = result['actionability_summary']

    assert summary['total'] > 0
    assert summary['autonomous'] >= 0
    assert summary['user_decision'] >= 0
    assert summary['hybrid'] >= 0

    # Verify counts match
    assert summary['total'] == (
        summary['autonomous'] +
        summary['user_decision'] +
        summary['hybrid']
    )

def test_autonomous_percentage_target():
    """Target >30% autonomous findings achieved."""
    result = adapter.review_target('/tmp/test', classify=True)
    summary = result['actionability_summary']

    if summary['total'] > 0:
        autonomous_pct = summary['autonomous'] / summary['total']
        assert autonomous_pct >= 0.3
```

---

#### FR4: Cost Optimization Tests

**TC-FR4.1: Cost Strategies**
```python
def test_aggressive_strategy_uses_only_free_providers():
    """Aggressive strategy uses 100% free providers."""
    result = adapter.review_target(
        '/tmp/test',
        cost_strategy='aggressive'
    )

    # Verify only free providers used
    providers = result['llm_metadata']['providers_used']
    free_providers = ['openrouter_free', 'groq']
    assert all(p in free_providers for p in providers)

def test_balanced_strategy_mixes_providers():
    """Balanced strategy mixes free and paid providers."""
    result = adapter.review_target(
        '/tmp/test',
        cost_strategy='balanced'
    )

    # Should have mix of free and paid
    providers = result['llm_metadata']['providers_used']
    assert len(providers) > 1

def test_cost_reduction_target():
    """Target 50%+ cost reduction achieved."""
    # Calculate cost vs baseline
    baseline_cost = calculate_baseline_cost()
    optimized_cost = calculate_optimized_cost('balanced')

    reduction = (baseline_cost - optimized_cost) / baseline_cost
    assert reduction >= 0.5
```

---

#### FR5: Code Compression Tests

**TC-FR5.1: Compression Configuration**
```python
def test_compression_disabled_by_default():
    """Compression is opt-in (disabled by default)."""
    executor = EnhancedQualityExecutor('/tmp/test')
    assert executor.compress_code == False

def test_compress_threshold_configurable():
    """Compression threshold is configurable."""
    executor = EnhancedQualityExecutor(
        '/tmp/test',
        compress_code=True,
        compress_threshold=5000
    )
    assert executor.compress_threshold == 5000
```

**TC-FR5.2: Compression Integration**
```python
def test_large_project_auto_compressed():
    """Projects >10k lines auto-compressed."""
    # Create test project with 15k lines
    large_project = create_test_project(line_count=15000)

    result = adapter.review_target(
        large_project,
        compress=True
    )

    assert result['compression']['enabled'] == True
    assert result['compression']['original_tokens'] > result['compression']['compressed_tokens']

def test_token_savings_target():
    """Target 89% token savings achieved."""
    result = adapter.review_target('/tmp/test', compress=True)

    if result['compression']['enabled']:
        compression_ratio = (
            1 - (result['compression']['compressed_tokens'] / result['compression']['original_tokens'])
        )
        assert compression_ratio >= 0.89
```

---

#### FR6: Consensus Metrics Tests

**TC-FR6.1: Consensus Scoring**
```python
def test_consensus_score_calculated():
    """Consensus score calculated for each finding."""
    result = adapter.review_target('/tmp/test')

    findings = result['consensus_findings']
    for finding in findings:
        assert 'consensus' in finding
        assert 'score' in finding['consensus']
        assert 0.0 <= finding['consensus']['score'] <= 1.0

def test_agreement_levels_determined():
    """Agreement level determined correctly."""
    result = adapter.review_target('/tmp/test')

    findings = result['consensus_findings']
    for finding in findings:
        level = finding['consensus']['level']
        assert level in ['high', 'medium', 'low']

        if level == 'high':
            assert finding['consensus']['agreeing_providers'] >= 2
```

---

### AC3: Integration Tests

#### Test Scenario: End-to-End Quality Gate
```python
def test_full_quality_gate_with_all_enhancements():
    """Full quality gate execution with all enhancements."""

    # Setup
    executor = EnhancedQualityExecutor(
        working_dir='/tmp/test_project',
        review_mode='mid',
        focus_areas=['security', 'bugs', 'performance'],
        verify_findings=True,
        classify_findings=True,
        cost_strategy='balanced',
        compress_code=True
    )

    # Execute
    results = executor.execute_cognitive_review_phase()

    # Assertions
    assert results['phase'] == 'cognitive_review'
    assert results['tool_status']['zen_cognitive_review'] == 'completed'

    # Check zen review results
    zen_review = results['zen_review']
    assert zen_review['success'] == True
    assert 'consensus_findings' in zen_review

    # Check verification
    assert zen_review['verified'] == True
    assert 'verification' in zen_review

    # Check classification
    assert 'actionability_summary' in zen_review
    assert zen_review['actionability_summary']['total'] > 0

    # Check consensus
    assert 'consensus_summary' in zen_review

    # Check cost
    assert 'cost_summary' in zen_review

    # Check compression
    assert 'compression' in zen_review
```

---

## 7. Success Metrics

### SM1: Feature Coverage
- [ ] All 12 review categories accessible
- [ ] Universal verification available for all reviews
- [ ] Actionability classification integrated
- [ ] Cost optimization with 3 strategies
- [ ] Code compression for large projects
- [ ] Consensus metrics exposed

### SM2: Performance Targets
- [ ] Gate 6 execution time within 30% of baseline
- [ ] Verification completes in <60 seconds
- [ ] Compression overhead <10 seconds
- [ ] 50%+ cost reduction achieved
- [ ] 89% token savings for large projects

### SM3: Quality Improvements
- [ ] >80% false positives filtered by verification
- [ ] >30% findings classified as autonomous
- [ ] >70% high-agreement findings in chad mode
- [ ] Consensus score correlates with finding quality

### SM4: Backward Compatibility
- [ ] 100% of legacy configs work unchanged
- [ ] API stability maintained
- [ ] Existing tests pass without modification

### SM5: Test Coverage
- [ ] 90%+ code coverage for new code
- [ ] All acceptance criteria have automated tests
- [ ] Integration tests cover full workflows

---

## 8. Risk Mitigation

### RM1: Backward Compatibility Risk
**Risk**: Breaking changes to existing configs
**Mitigation**:
- Comprehensive legacy area mapping
- Extensive testing with existing configs
- Opt-in defaults for new features
- Migration guide and documentation

### RM2: Performance Degradation Risk
**Risk**: Enhancements slow down quality gates
**Mitigation**:
- Performance budgets for each feature
- Async execution where possible
- Lazy loading of optional components
- Benchmarking and optimization

### RM3: Configuration Complexity Risk
**Risk**: Too many configuration options overwhelm users
**Mitigation**:
- Sensible defaults for all features
- Progressive disclosure (basic → advanced options)
- Clear documentation and examples
- Configuration validation

### RM4: LLM Dependency Risk
**Risk**: LLM unavailability breaks gates
**Mitigation**:
- Maintain deterministic gates 1-5
- Graceful degradation when LLM unavailable
- Clear error messages
- Offline mode documentation

---

## 9. Implementation Priorities

### Phase 1: Core Enhancements (Week 1)
**Priority**: High
- [ ] FR1: Focus area expansion (3 → 12 categories)
- [ ] FR2: Universal verification system
- [ ] FR3: Actionability classification integration

**Deliverables**:
- Updated category mapping
- Verification integration
- Classification integration
- Basic tests

### Phase 2: Cost & Performance (Week 2)
**Priority**: High
- [ ] FR4: Cost optimization with free providers
- [ ] FR5: Code compression for large projects

**Deliverables**:
- Cost strategy implementation
- Provider selection logic
- Compression integration
- Performance tests

### Phase 3: Quality Metrics (Week 3)
**Priority**: Medium
- [ ] FR6: Consensus quality metrics
- [ ] Enhanced reporting and display
- [ ] CLI flag additions

**Deliverables**:
- Consensus scoring
- Enhanced reports
- CLI enhancements
- Documentation

### Phase 4: Testing & Validation (Week 4)
**Priority**: High
- [ ] Comprehensive test suite
- [ ] Integration tests
- [ ] Performance benchmarks
- [ ] Documentation completion

**Deliverables**:
- 90%+ test coverage
- Performance validation
- Complete documentation
- Migration guide

---

## 10. Dependencies

### External Dependencies
- `zen.lib.finding_verifier` - Verification system
- `zen.lib.actionability_classifier` - Classification system
- `zen_integration.provider_wrapper` - Provider management
- `zen_integration.api_key_manager` - API key management

### Internal Dependencies
- `quality.zen_review_adapter` - Zen adapter
- `quality.enhanced_execution` - Enhanced executor
- `quality.qual-gate.py` - CLI interface

### Documentation Dependencies
- Configuration schema documentation
- CLI reference
- Migration guide
- Troubleshooting guide

---

## 11. Sign-Off

### Requirements Review Checklist
- [ ] All functional requirements defined
- [ ] All technical requirements specified
- [ ] All data requirements documented
- [ ] All integration requirements detailed
- [ ] All non-functional requirements listed
- [ ] All acceptance criteria testable
- [ ] All success metrics measurable
- [ ] All risks identified with mitigations

### Approval
- [ ] Requirements reviewed by development team
- [ ] Requirements approved by stakeholders
- [ ] Test plan reviewed by QA team
- [ ] Documentation plan reviewed by tech writing
- [ ] Implementation timeline approved

---

**Document Status**: Requirements Analysis Complete
**Next Phase**: Research Intelligence (/research)
**Estimated Implementation Time**: 4 weeks
**Risk Level**: Medium (mitigated by backward compatibility focus)
