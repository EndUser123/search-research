# GREEN Phase Guide: Single Responsibility Principle Adherence

## Purpose

Implement minimal code to pass RED phase tests while strictly following the Single Responsibility Principle (SRP) and CSF NIP constitutional standards for solo developer optimization.

## Implementation Strategy

### Core Principles

1. **One Reason to Change**: Each component should have exactly one reason to change
2. **Minimal Viable Implementation**: Implement only what's needed to pass tests
3. **Solo Developer Friendly**: Keep complexity low and maintainability high
4. **Evidence-Based**: Every implementation decision must be justified by test requirements

## Template Structure

### 1. Single Responsibility Error Classifier Implementation

```python
"""
GREEN Phase: Single Responsibility Error Classification
CSF NIP Compliance: Solo Developer Optimization & Force Multiplier
CWO12 Integration: Phase 2 - Task Decomposition Assignment
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Single Responsibility: Error Classification Only
class ErrorClassifier:
    """
    Single Responsibility: Classifies system errors into categories
    - One reason to change: Error classification rules change
    - No other responsibilities: no logging, no recovery, no notification
    """

    def __init__(self):
        self._classification_rules = {
            "validation_error": self._classify_validation_error,
            "configuration_error": self._classify_configuration_error,
            "runtime_error": self._classify_runtime_error,
            "resource_error": self._classify_resource_error,
            "communication_error": self._classify_communication_error,
            "security_error": self._classify_security_error
        }

    def classify(self, error_input: Dict[str, Any]) -> 'ErrorResult':
        """
        Classify error based on input characteristics
        SRP: Only performs classification, nothing else
        """
        error_type = self._determine_error_type(error_input)
        severity = self._determine_severity(error_input, error_type)

        return ErrorResult(
            type=error_type,
            severity=severity,
            message=self._generate_message(error_type, error_input),
            recovery_possible=self._assess_recovery_possibility(error_type, error_input)
        )

    def _determine_error_type(self, error_input: Dict[str, Any]) -> str:
        """Private method: Determine error type from input"""
        if "validation" in str(error_input).lower():
            return "validation_error"
        elif "resource" in str(error_input).lower() or any(key in error_input for key in ["memory", "cpu", "disk"]):
            return "resource_error"
        elif "communication" in str(error_input).lower() or "network" in str(error_input).lower():
            return "communication_error"
        elif "security" in str(error_input).lower():
            return "security_error"
        elif "configuration" in str(error_input).lower():
            return "configuration_error"
        else:
            return "runtime_error"

    def _determine_severity(self, error_input: Dict[str, Any], error_type: str) -> str:
        """Private method: Determine severity based on error characteristics"""
        if error_type == "security_error":
            return "critical" if "breach" in str(error_input).lower() else "high"
        elif error_type == "resource_error":
            return "critical" if any(value > 0.9 for value in error_input.values() if isinstance(value, (int, float))) else "high"
        elif error_type == "validation_error":
            return "medium" if "failed" in str(error_input).lower() else "low"
        else:
            return "medium"

    def _generate_message(self, error_type: str, error_input: Dict[str, Any]) -> str:
        """Private method: Generate appropriate error message"""
        return f"{error_type.replace('_', ' ').title()} detected: {str(error_input)[:100]}"

    def _assess_recovery_possibility(self, error_type: str, error_input: Dict[str, Any]) -> bool:
        """Private method: Assess if error can be recovered from"""
        recoverable_types = ["validation_error", "communication_error", "configuration_error"]
        return error_type in recoverable_types

@dataclass
class ErrorResult:
    """Single Responsibility: Error classification result container"""
    type: str
    severity: str
    message: str
    recovery_possible: bool
```

### 2. Single Responsibility Resource Monitor Implementation

```python
class ResourceMonitor:
    """
    Single Responsibility: Monitor system resource usage
    - One reason to change: Resource monitoring requirements change
    - No other responsibilities: no alerting, no recovery, no storage
    """

    def __init__(self):
        pass  # Minimal initialization

    def check_resource_status(self) -> 'ResourceStatus':
        """
        Check current resource usage
        SRP: Only monitors, no action taken
        """
        import psutil

        return ResourceStatus(
            cpu_usage=psutil.cpu_percent() / 100,
            memory_usage=psutil.virtual_memory().percent / 100,
            disk_usage=psutil.disk_usage('/').percent / 100,
            active_processes=len(psutil.pids())
        )

    def identify_high_usage(self, status: 'ResourceStatus', threshold: float = 0.8) -> List[str]:
        """
        Identify resources above threshold
        SRP: Only identification, no correction
        """
        high_usage = []
        if status.cpu_usage > threshold:
            high_usage.append("cpu")
        if status.memory_usage > threshold:
            high_usage.append("memory")
        if status.disk_usage > threshold:
            high_usage.append("disk")
        return high_usage

@dataclass
class ResourceStatus:
    """Single Responsibility: Resource status container"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_processes: int
```

### 3. Single Responsibility Performance Analyzer Implementation

```python
class PerformanceAnalyzer:
    """
    Single Responsibility: Analyze performance metrics
    - One reason to change: Performance analysis logic changes
    - No other responsibilities: no monitoring, no optimization, no reporting
    """

    def analyze_response_time(self, response_times: List[float]) -> 'PerformanceAnalysis':
        """
        Analyze response time performance
        SRP: Only analysis, no optimization suggestions
        """
        if not response_times:
            return PerformanceAnalysis(0.0, 0.0, 0.0, "no_data")

        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        # Simple performance classification
        if avg_time > 2.0:
            performance_level = "poor"
        elif avg_time > 1.0:
            performance_level = "moderate"
        else:
            performance_level = "good"

        return PerformanceAnalysis(avg_time, max_time, min_time, performance_level)

    def detect_anomalies(self, measurements: List[float], threshold_factor: float = 2.0) -> List[int]:
        """
        Detect performance anomalies in measurements
        SRP: Only detection, no correction
        """
        if len(measurements) < 3:
            return []

        avg = sum(measurements) / len(measurements)
        std_dev = (sum((x - avg) ** 2 for x in measurements) / len(measurements)) ** 0.5

        anomalies = []
        for i, measurement in enumerate(measurements):
            if abs(measurement - avg) > threshold_factor * std_dev:
                anomalies.append(i)

        return anomalies

@dataclass
class PerformanceAnalysis:
    """Single Responsibility: Performance analysis result"""
    average: float
    maximum: float
    minimum: float
    performance_level: str
```

### 4. Implementation Guidelines by RED Phase Test Type

#### 4.1 System Error Detection Implementation

```python
# Minimal implementation to pass RED phase tests
def classify_system_error(error_input: Dict[str, Any]) -> ErrorResult:
    """
    GREEN Phase: Minimal implementation for RED phase test
    SRP: Only classifies errors, no other functionality
    """
    classifier = ErrorClassifier()
    return classifier.classify(error_input)

def detect_resource_error(resource_scenario: Dict[str, Any]) -> ErrorResult:
    """
    GREEN Phase: Minimal resource error detection
    SRP: Only detects resource issues
    """
    monitor = ResourceMonitor()
    status = monitor.check_resource_status()

    # Convert scenario to detection logic
    high_usage = monitor.identify_high_usage(status, threshold=0.85)

    if high_usage:
        return ErrorResult(
            type="resource_error",
            severity="critical" if len(high_usage) > 1 else "high",
            message=f"Resource pressure detected: {', '.join(high_usage)}",
            recovery_possible=True
        )

    return ErrorResult(
        type="resource_error",
        severity="low",
        message="No resource issues detected",
        recovery_possible=True
    )

def classify_communication_error(comm_scenario: Dict[str, Any]) -> ErrorResult:
    """
    GREEN Phase: Minimal communication error classification
    SRP: Only classifies communication errors
    """
    if "connection_timeout" in comm_scenario:
        return ErrorResult(
            type="communication_error",
            severity="high",
            message=f"Connection timeout to {comm_scenario.get('host', 'unknown')}",
            recovery_possible=True
        )
    elif "http_status" in comm_scenario and comm_scenario["http_status"] >= 500:
        return ErrorResult(
            type="communication_error",
            severity="high",
            message=f"HTTP {comm_scenario['http_status']} error at {comm_scenario.get('endpoint', 'unknown')}",
            recovery_possible=True
        )
    else:
        return ErrorResult(
            type="communication_error",
            severity="medium",
            message="Communication issue detected",
            recovery_possible=True
        )

def classify_security_error(security_scenario: Dict[str, Any]) -> ErrorResult:
    """
    GREEN Phase: Minimal security error classification
    SRP: Only classifies security errors
    """
    return ErrorResult(
        type="security_error",
        severity="critical" if "breach" in str(security_scenario).lower() else "high",
        message="Security violation detected",
        recovery_possible=False,
        requires_immediate_action=True
    )
```

#### 4.2 Performance Bottleneck Detection Implementation

```python
def identify_cpu_bottleneck(cpu_scenario: Dict[str, Any]) -> 'BottleneckResult':
    """
    GREEN Phase: Minimal CPU bottleneck identification
    SRP: Only identifies CPU issues
    """
    utilization = cpu_scenario.get("utilization", 0)

    return BottleneckResult(
        type="cpu_intensive",
        severity="critical" if utilization >= 0.95 else "high",
        location="system_cpu",
        impact=f"CPU utilization at {utilization:.1%}",
        metrics={"utilization": utilization},
        threshold_exceeded=max(0, utilization - 0.85),
        recommended_action="Investigate high CPU processes"
    )

def detect_memory_leak(memory_scenario: Dict[str, Any]) -> 'BottleneckResult':
    """
    GREEN Phase: Minimal memory leak detection
    SRP: Only detects memory issues
    """
    if "heap_growth" in memory_scenario:
        growth = memory_scenario["heap_growth"]
        return BottleneckResult(
            type="memory_intensive",
            severity="critical" if growth > 0.8 else "high",
            location="application_memory",
            impact=f"Heap growth at {growth:.1%}",
            metrics={"heap_growth": growth},
            threshold_exceeded=max(0, growth - 0.6),
            recommended_action="Profile memory usage for leaks"
        )

    return BottleneckResult(
        type="memory_intensive",
        severity="low",
        location="application_memory",
        impact="No significant memory issues detected",
        metrics={},
        threshold_exceeded=0,
        recommended_action="Continue monitoring"
    )

def analyze_io_bottleneck(io_scenario: Dict[str, Any]) -> 'BottleneckResult':
    """
    GREEN Phase: Minimal I/O bottleneck analysis
    SRP: Only analyzes I/O issues
    """
    if "disk_utilization" in io_scenario:
        utilization = io_scenario["disk_utilization"]
        return BottleneckResult(
            type="io_intensive",
            severity="critical" if utilization >= 0.95 else "high",
            location="disk_io",
            impact=f"Disk utilization at {utilization:.1%}",
            metrics={"disk_utilization": utilization},
            threshold_exceeded=max(0, utilization - 0.85),
            recommended_action="Optimize disk operations or upgrade storage"
        )

    return BottleneckResult(
        type="io_intensive",
        severity="low",
        location="io_subsystem",
        impact="No significant I/O issues detected",
        metrics={},
        threshold_exceeded=0,
        recommended_action="Continue monitoring"
    )
```

## Implementation Quality Checklist

### Single Responsibility Validation

- [ ] **One Reason to Change**: Each class has exactly one reason to change
- [ ] **Cohesive Methods**: All methods within a class contribute to the same responsibility
- [ ] **No Side Effects**: Methods only perform their primary responsibility
- [ ] **Minimal Dependencies**: Classes depend only on what they need

### GREEN Phase Success Criteria

- [ ] **Tests Pass**: All RED phase tests now pass
- [ ] **Minimal Implementation**: Only essential code is implemented
- [ ] **No Gold Plating**: No unnecessary features or optimizations
- [ ] **SRP Compliance**: Single Responsibility Principle strictly followed

### Constitutional Compliance

- [ ] **Evidence-Based**: Each implementation directly addresses test requirements
- [ ] **Solo Developer Friendly**: Code is simple, maintainable, and understandable
- [ ] **Force Multiplier**: Components can be easily combined and reused
- [ ] **No Enterprise Bloat**: Avoids over-engineering and unnecessary complexity

## CWO12 Integration

### Phase 2 Integration Points

- **Task Decomposition**: Single responsibility components enable clear task assignment
- **Execution Monitoring**: Each component can be monitored independently
- **Quality Validation**: SRP makes it easier to validate individual component quality

### Phase 3 Preparation

- **Constitutional Validation**: Each component can be validated independently
- **Metrics Collection**: Clear separation enables accurate performance measurement
- **Pattern Recognition**: SRP patterns can be identified and stored

## Transition to REFACTOR Phase

### Preparation Checklist

- [ ] All RED phase tests pass
- [ ] Code coverage meets requirements
- [ ] Performance thresholds achieved
- [ ] SRP violations identified for refactoring
- [ ] Refactoring opportunities documented

### Common Refactoring Opportunities

1. **Extract Method**: Break down complex methods
2. **Extract Class**: Separate multiple responsibilities
3. **Replace Conditional with Polymorphism**: Reduce complexity
4. **Introduce Parameter Object**: Simplify method signatures
5. **Compose Method**: Improve readability and maintainability

This GREEN phase guide ensures minimal, SRP-compliant implementations that satisfy RED phase tests while maintaining CSF NIP constitutional standards and CWO12 integration requirements.
