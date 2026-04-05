# GREEN Phase Guide: Minimum Viable Implementation Patterns

## Purpose

Provide concrete patterns and examples for implementing the minimum viable code needed to pass RED phase tests while adhering to CSF NIP constitutional standards for solo developer optimization.

## Core Implementation Philosophy

### Minimum Viable Principles

1. **Just Enough Code**: Implement only what tests require
2. **No Premature Optimization**: Solve the problem, don't over-engineer
3. **Simplicity First**: Choose the simplest solution that works
4. **Evidence-Driven**: Every line of code justified by test requirements
5. **Solo Developer Friendly**: Low cognitive overhead, high maintainability

## Pattern Templates

### 1. Data Transfer Object (DTO) Pattern

```python
"""
Minimum Viable DTO Pattern
Purpose: Simple data container with no behavior
SRP: Only holds data, no business logic
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class ErrorResultDTO:
    """
    Minimum Viable Error Result Container
    - Only data, no methods
    - Immutable by default
    - Serializable for testing
    """
    type: str
    severity: str
    message: str
    recovery_possible: bool
    requires_immediate_action: bool = False
    evidence: Dict[str, Any] = None

    def __post_init__(self):
        """Minimal validation for essential fields"""
        if self.evidence is None:
            self.evidence = {}

@dataclass
class PerformanceMetricDTO:
    """
    Minimum Viable Performance Metric
    - Only essential performance data
    - No analysis logic
    - Simple for testing
    """
    name: str
    value: float
    unit: str
    threshold: float
    timestamp: str
    status: str = "unknown"

    @property
    def is_above_threshold(self) -> bool:
        """Minimal derived property for test convenience"""
        return self.value > self.threshold
```

### 2. Simple Classifier Pattern

```python
"""
Minimum Viable Classifier Pattern
Purpose: Categorize inputs based on simple rules
SRP: Only performs classification
"""

class SimpleClassifier:
    """
    Minimum Viable Error Classifier
    - No complex algorithms
    - Simple rule-based logic
    - Easy to test and maintain
    """

    def __init__(self, rules: Dict[str, Any] = None):
        self.rules = rules or self._default_rules()

    def classify(self, input_data: Dict[str, Any]) -> str:
        """
        Simple classification using keyword matching
        GREEN Phase: Minimal implementation for RED tests
        """
        input_str = str(input_data).lower()

        # Simple keyword-based classification
        for category, keywords in self.rules.items():
            if any(keyword in input_str for keyword in keywords):
                return category

        return "unknown"

    def _default_rules(self) -> Dict[str, List[str]]:
        """Default classification rules"""
        return {
            "validation_error": ["validation", "invalid", "failed"],
            "security_error": ["security", "unauthorized", "breach"],
            "resource_error": ["memory", "cpu", "disk", "resource"],
            "communication_error": ["network", "connection", "timeout", "http"],
            "configuration_error": ["config", "setting", "parameter"],
            "runtime_error": ["exception", "error", "failure"]
        }

class SeverityClassifier:
    """
    Minimum Viable Severity Classifier
    - Simple threshold-based logic
    - No complex scoring algorithms
    - Deterministic results
    """

    def classify_severity(self, error_type: str, context: Dict[str, Any]) -> str:
        """
        Simple severity classification
        GREEN Phase: Minimal logic for test requirements
        """
        # Simple rule-based severity mapping
        severity_map = {
            "security_error": "critical" if "breach" in str(context).lower() else "high",
            "resource_error": "critical" if self._check_critical_resource(context) else "high",
            "validation_error": "medium",
            "communication_error": "medium" if "timeout" in str(context).lower() else "high",
            "configuration_error": "medium",
            "runtime_error": "low"
        }

        return severity_map.get(error_type, "medium")

    def _check_critical_resource(self, context: Dict[str, Any]) -> bool:
        """Simple critical resource check"""
        for value in context.values():
            if isinstance(value, (int, float)) and value > 0.9:
                return True
        return False
```

### 3. Simple Monitor Pattern

```python
"""
Minimum Viable Monitor Pattern
Purpose: Observe system state without intervention
SRP: Only monitors, no action
"""

class SimpleResourceMonitor:
    """
    Minimum Viable Resource Monitor
    - Basic system resource checking
    - No complex analysis
    - Simple status reporting
    """

    def __init__(self):
        # Minimal initialization - no complex setup
        pass

    def check_status(self) -> Dict[str, float]:
        """
        Simple resource status check
        GREEN Phase: Basic implementation for RED tests
        """
        try:
            import psutil
            return {
                "cpu_usage": psutil.cpu_percent() / 100,
                "memory_usage": psutil.virtual_memory().percent / 100,
                "disk_usage": psutil.disk_usage('/').percent / 100
            }
        except ImportError:
            # Fallback for testing without psutil
            return {
                "cpu_usage": 0.5,  # Mock values for testing
                "memory_usage": 0.6,
                "disk_usage": 0.4
            }

    def is_resource_critical(self, status: Dict[str, float], threshold: float = 0.9) -> bool:
        """
        Simple critical resource detection
        GREEN Phase: Minimal logic for test requirements
        """
        return any(usage > threshold for usage in status.values())

class SimplePerformanceMonitor:
    """
    Minimum Viable Performance Monitor
    - Basic timing and measurement
    - No complex analysis
    - Simple metric collection
    """

    def __init__(self):
        self.measurements: List[float] = []

    def measure_operation(self, operation_name: str, operation_func) -> float:
        """
        Simple operation timing
        GREEN Phase: Basic measurement for test requirements
        """
        import time
        start_time = time.time()
        try:
            operation_func()
        except Exception:
            # Still measure time even if operation fails
            pass
        end_time = time.time()

        duration = end_time - start_time
        self.measurements.append(duration)
        return duration

    def get_average_time(self) -> float:
        """Simple average calculation"""
        return sum(self.measurements) / len(self.measurements) if self.measurements else 0.0

    def is_performance_acceptable(self, threshold: float) -> bool:
        """Simple performance check"""
        avg_time = self.get_average_time()
        return avg_time <= threshold
```

### 4. Simple Validator Pattern

```python
"""
Minimum Viable Validator Pattern
Purpose: Validate inputs without complex business logic
SRP: Only performs validation
"""

class SimpleInputValidator:
    """
    Minimum Viable Input Validator
    - Basic input checking
    - No complex validation rules
    - Simple pass/fail results
    """

    def __init__(self):
        # Minimal initialization
        pass

    def validate_email(self, email: str) -> bool:
        """
        Simple email validation
        GREEN Phase: Minimal implementation for test requirements
        """
        if not email or "@" not in email:
            return False
        return True

    def validate_numeric_range(self, value: Any, min_val: float, max_val: float) -> bool:
        """
        Simple numeric range validation
        GREEN Phase: Basic numeric checking
        """
        try:
            num_value = float(value)
            return min_val <= num_value <= max_val
        except (ValueError, TypeError):
            return False

    def validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Simple required field validation
        GREEN Phase: Basic field presence checking
        """
        return all(field in data and data[field] is not None for field in required_fields)

class SimpleComplianceValidator:
    """
    Minimum Viable Compliance Validator
    - Basic rule checking
    - No complex compliance logic
    - Simple compliance status
    """

    def __init__(self, compliance_rules: Dict[str, Any] = None):
        self.rules = compliance_rules or {}

    def check_compliance(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Simple compliance checking
        GREEN Phase: Basic rule evaluation
        """
        results = {}

        # Simple rule examples
        if "data_retention" in self.rules:
            retention_days = data.get("retention_days", 0)
            max_days = self.rules["data_retention"]["max_days"]
            results["data_retention"] = retention_days <= max_days

        if "consent_rate" in self.rules:
            consent_rate = data.get("consent_rate", 0)
            min_rate = self.rules["consent_rate"]["min_rate"]
            results["consent_rate"] = consent_rate >= min_rate

        return results

    def is_compliant(self, compliance_results: Dict[str, bool]) -> bool:
        """Simple overall compliance check"""
        return all(compliance_results.values())
```

### 5. Simple Analyzer Pattern

```python
"""
Minimum Viable Analyzer Pattern
Purpose: Analyze data without complex algorithms
SRP: Only performs analysis
"""

class SimpleTrendAnalyzer:
    """
    Minimum Viable Trend Analyzer
    - Basic trend detection
    - No complex statistical analysis
    - Simple trend classification
    """

    def analyze_trend(self, values: List[float]) -> str:
        """
        Simple trend analysis
        GREEN Phase: Basic trend detection for test requirements
        """
        if len(values) < 2:
            return "insufficient_data"

        # Simple trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]

        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)

        if second_avg > first_avg * 1.1:
            return "increasing"
        elif second_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"

    def detect_anomalies(self, values: List[float], threshold_factor: float = 2.0) -> List[int]:
        """
        Simple anomaly detection
        GREEN Phase: Basic statistical outlier detection
        """
        if len(values) < 3:
            return []

        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5

        anomalies = []
        for i, value in enumerate(values):
            if abs(value - avg) > threshold_factor * std_dev:
                anomalies.append(i)

        return anomalies

class SimplePerformanceAnalyzer:
    """
    Minimum Viable Performance Analyzer
    - Basic performance metrics
    - No complex analysis
    - Simple performance classification
    """

    def analyze_response_times(self, response_times: List[float]) -> Dict[str, Any]:
        """
        Simple response time analysis
        GREEN Phase: Basic metric calculation
        """
        if not response_times:
            return {
                "average": 0.0,
                "maximum": 0.0,
                "minimum": 0.0,
                "performance_level": "no_data"
            }

        avg = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        # Simple performance classification
        if avg > 2.0:
            level = "poor"
        elif avg > 1.0:
            level = "moderate"
        else:
            level = "good"

        return {
            "average": avg,
            "maximum": max_time,
            "minimum": min_time,
            "performance_level": level
        }

    def calculate_efficiency_score(self, actual_performance: float, target_performance: float) -> float:
        """
        Simple efficiency calculation
        GREEN Phase: Basic efficiency metric
        """
        if target_performance <= 0:
            return 0.0

        efficiency = target_performance / actual_performance
        return min(1.0, efficiency)  # Cap at 100%
```

## Implementation Examples by Problem Type

### System Error Detection Example

```python
"""
Minimum Viable Implementation: System Error Detection
GREEN Phase: Passes RED tests with minimal code
"""

def classify_system_error(error_input: Dict[str, Any]) -> ErrorResultDTO:
    """
    Minimum viable system error classification
    - Simple pattern matching
    - No complex analysis
    - Passes all RED tests
    """
    classifier = SimpleClassifier()
    severity_classifier = SeverityClassifier()

    error_type = classifier.classify(error_input)
    severity = severity_classifier.classify_severity(error_type, error_input)

    return ErrorResultDTO(
        type=error_type,
        severity=severity,
        message=f"{error_type.replace('_', ' ').title()} detected",
        recovery_possible=error_type not in ["security_error"],
        requires_immediate_action=error_type == "security_error"
    )

def detect_resource_error(resource_scenario: Dict[str, Any]) -> ErrorResultDTO:
    """
    Minimum viable resource error detection
    - Simple threshold checking
    - No complex monitoring
    - Passes RED tests
    """
    monitor = SimpleResourceMonitor()
    status = monitor.check_status()

    # Simple threshold-based detection
    if monitor.is_resource_critical(status, threshold=0.85):
        return ErrorResultDTO(
            type="resource_error",
            severity="critical",
            message="Resource usage above critical threshold",
            recovery_possible=True
        )

    return ErrorResultDTO(
        type="resource_error",
        severity="low",
        message="Resource usage within normal limits",
        recovery_possible=True
    )
```

### Business Finding Validation Example

```python
"""
Minimum Viable Implementation: Business Finding Validation
GREEN Phase: Simple business logic validation
"""

def identify_financial_anomalies(financial_data: Dict[str, Any]) -> List[Any]:
    """
    Minimum viable financial anomaly detection
    - Simple statistical analysis
    - No complex machine learning
    - Passes RED tests
    """
    monthly_revenue = financial_data.get("monthly_revenue", [])
    expected_range = financial_data.get("expected_range", [0, float('inf')])

    anomalies = []
    for i, revenue in enumerate(monthly_revenue):
        if revenue < expected_range[0] or revenue > expected_range[1]:
            anomalies.append({
                "month": i,
                "revenue": revenue,
                "type": "revenue_spike" if revenue > expected_range[1] else "revenue_drop"
            })

    return anomalies

def analyze_cost_patterns(cost_data: Dict[str, Any]) -> List[Any]:
    """
    Minimum viable cost pattern analysis
    - Simple variance calculation
    - No complex forecasting
    - Passes RED tests
    """
    operational_costs = cost_data.get("operational_costs", {})
    historical_average = cost_data.get("historical_average", 0)
    variance_threshold = cost_data.get("variance_threshold", 0.2)

    findings = []
    for quarter, cost in operational_costs.items():
        variance = abs(cost - historical_average) / historical_average if historical_average else 0
        if variance > variance_threshold:
            findings.append({
                "quarter": quarter,
                "cost": cost,
                "variance": variance,
                "category": "financial_anomaly"
            })

    return findings
```

## Quality Assurance Checklist

### Minimum Viable Validation

- [ ] **RED Tests Pass**: All failing tests now pass
- [ ] **No Extra Features**: Only implemented what tests require
- [ ] **Simple Logic**: Avoided complex algorithms and data structures
- [ ] **Clear Naming**: Functions and variables clearly indicate purpose
- [ ] **Minimal Dependencies**: Limited external dependencies

### CSF NIP Compliance

- [ ] **Evidence-Based**: Each implementation directly addresses test requirements
- [ ] **Solo Developer Friendly**: Code is simple and maintainable
- [ ] **Force Multiplier**: Components can be easily reused
- [ ] **No Enterprise Bloat**: Avoided over-engineering

### CWO12 Integration

- [ ] **Phase 2 Ready**: Components can be used in task execution
- [ ] **Monitoring Ready**: Simple interfaces for performance monitoring
- [ ] **Quality Ready**: Clear interfaces for quality validation

## Common Pitfalls to Avoid

### Over-Engineering

1. **Complex Data Structures**: Use simple lists and dictionaries
2. **Advanced Algorithms**: Stick to basic statistical calculations
3. **Excessive Abstraction**: Avoid unnecessary classes and interfaces
4. **Premature Optimization**: Don't optimize beyond test requirements

### Under-Implementation

1. **Missing Edge Cases**: Ensure tests cover all scenarios
2. **Insufficient Validation**: Basic input validation is still needed
3. **Poor Error Handling**: Minimal error handling is required
4. **Inadequate Documentation**: Basic docstrings are necessary

This guide ensures minimum viable implementations that satisfy RED phase tests while maintaining simplicity and constitutional compliance for solo developer environments.
