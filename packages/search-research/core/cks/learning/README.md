# CKS Continuous Learning Framework

A comprehensive continuous learning system for usage pattern tracking, adaptive optimization, and knowledge quality scoring with evidence-based learning, built with CSF constitutional compliance.

## Architecture Overview

The CKS Learning Framework implements a multi-layer learning system with four core components:

1. **UsagePatternTracker** - Statistical pattern analysis and anomaly detection
2. **AdaptiveOptimizer** - Machine learning-based optimization engine
3. **KnowledgeQualityScorer** - Evidence-based quality assessment
4. **EvidenceBasedLearning** - Continuous improvement with validation loops

## Key Features

### Usage Pattern Tracking
- Real-time operation tracking with statistical analysis
- Peak hours detection and temporal pattern analysis
- Anomaly detection with configurable thresholds
- Resource usage monitoring and optimization opportunities
- Thread-safe concurrent operation support

### Adaptive Optimization
- Machine learning-driven optimization recommendations
- Auto-applicable optimizations with confidence scoring
- Performance bottleneck identification
- Multi-objective optimization (performance, quality, resources)
- System-wide optimization opportunities analysis

### Knowledge Quality Scoring
- Multi-dimensional quality assessment (accuracy, relevance, freshness, validation)
- Evidence-based scoring with confidence intervals
- Quality trend analysis and degradation detection
- Statistical validation with empirical evidence
- Quality improvement recommendations

### Evidence-Based Learning
- Continuous improvement cycles with validation
- Learning insight generation with confidence scoring
- Historical pattern analysis and trend detection
- Automated knowledge quality improvement
- Constitutional compliance validation

## Constitutional Requirements Compliance

### Solo Developer Optimization
- **Zero Background Services**: On-demand processing only
- **Single PC Deployment**: No clustering or distributed components
- **Minimal Resource Usage**: Efficient memory and CPU utilization
- **Controlled Threading**: Essential background threads only

### Evidence-Based Implementation
- **TDD Approach**: Comprehensive test coverage with real data
- **Real Data Validation**: No synthetic or mock test data
- **Statistical Analysis**: Evidence-based decision making
- **Continuous Validation**: Ongoing quality assurance

### Force Multiplier Integration
- **Multi-Graph Support**: Pattern, quality, optimization, and learning graphs
- **Adaptive Learning**: Self-improving system with feedback loops
- **Scalable Architecture**: Configurable limits and resource management
- **Intelligent Coordination**: Automated system optimization

### No Enterprise Bloat
- **Minimal Dependencies**: Core Python libraries only
- **Direct Implementation**: No unnecessary abstractions
- **Simple Configuration**: Straightforward setup and management
- **Focused Functionality**: Purpose-built for learning objectives

## Quick Start

### Basic Usage

```python
from cks.learning import ContinuousLearner, LearningConfig

# Create learner with default configuration
learner = ContinuousLearner()

# Track usage patterns
learner.track_usage("database", "query", 0.5, success=True)
learner.track_usage("cache", "get", 0.1, success=True)

# Assess knowledge quality
evidence = [
    {"type": "accuracy", "value": 0.9, "data": {"source": "verified"}},
    {"type": "relevance", "value": 0.8, "data": {"context": "current"}}
]
metrics = learner.assess_quality("knowledge_id", evidence)

# Get insights and optimizations
insights = learner.get_insights()
top_patterns = learner.get_patterns()

# Check system status
status = learner.get_system_status()
print(f"Patterns tracked: {status['components']['pattern_tracker']['patterns_tracked']}")
print(f"Knowledge assessed: {status['components']['quality_scorer']['knowledge_assessed']}")

# Graceful shutdown
learner.shutdown()
```

### Advanced Configuration

```python
from cks.learning import LearningConfig

config = LearningConfig(
    database_path="data/my_learning.db",
    pattern_window_size=1000,
    confidence_threshold=0.8,
    auto_optimization_enabled=True,
    anomaly_detection_enabled=True,
    constitutional_validation=True
)

learner = ContinuousLearner(config)
```

### Context Manager Usage

```python
from cks.learning import continuous_learning_session

with continuous_learning_session() as learner:
    # Automatic resource management
    learner.track_usage("api", "request", 1.2, success=True)
    metrics = learner.assess_quality("my_knowledge", evidence)
    # Automatic shutdown on context exit
```

## Component APIs

### UsagePatternTracker

```python
# Track operations
tracker.track_operation(component, operation, duration, success, metadata)

# Get patterns
patterns = tracker.get_patterns_by_component("database")
top_patterns = tracker.get_top_patterns(limit=10)

# Analyze specific pattern
pattern = tracker.get_pattern(pattern_id)
```

### AdaptiveOptimizer

```python
# Generate optimizations
insights = optimizer.generate_optimizations()

# Get optimization history
history = optimizer.get_optimization_history(limit=50)
```

### KnowledgeQualityScorer

```python
# Assess knowledge quality
metrics = scorer.assess_knowledge_quality(knowledge_id, evidence)

# Get quality rankings
top_quality = scorer.get_top_quality_knowledge(limit=10)
low_quality = scorer.get_low_quality_knowledge(threshold=0.5)
```

### EvidenceBasedLearning

```python
# Get insights by type
pattern_insights = learning.get_insights(insight_type="pattern")
quality_insights = learning.get_insights(insight_type="quality")

# Get learning history
history = learning.get_learning_history(limit=50)
```

## Configuration Options

### LearningConfig Parameters

- `database_path`: SQLite database file path
- `pattern_window_size`: Number of operations to analyze (default: 1000)
- `confidence_threshold`: Minimum confidence for auto-optimizations (default: 0.7)
- `auto_optimization_enabled`: Enable automatic optimizations (default: False)
- `anomaly_detection_enabled`: Enable anomaly detection (default: True)
- `constitutional_validation`: Enable CSF compliance (default: True)
- `max_insights_retained`: Maximum insights to keep (default: 1000)
- `quality_weights`: Weights for quality scoring dimensions

## Quality Scoring Dimensions

### Accuracy Score
- Evidence-based accuracy assessment
- Source verification and validation
- Confidence interval calculation

### Relevance Score
- Context relevance assessment
- Timeliness and applicability
- Usage pattern correlation

### Freshness Score
- Content age analysis
- Update frequency tracking
- Staleness detection

### Validation Score
- Peer review validation
- Automated validation results
- Cross-validation metrics

### Usage Score
- Frequency of use
- User feedback integration
- Performance metrics

## Compliance Validation

### Constitutional Requirements

```python
from cks.learning.validation import validate_learning_framework_compliance

# Validate compliance
constitutional_report, csf_nip_report = validate_learning_framework_compliance(learner)

print(f"Constitutional compliance: {constitutional_report.overall_compliance.value}")
print(f"CSF compliance: {csf_nip_report.overall_compliance.value}")
```

### Validation Areas

1. **Solo Developer Optimization**
   - No unauthorized background services
   - On-demand processing only
   - Single PC deployment verification

2. **Evidence-Based Implementation**
   - TDD approach validation
   - Real data usage verification
   - No synthetic test data

3. **Force Multiplier Integration**
   - Multi-graph capability
   - Adaptive learning systems
   - Scalable architecture

4. **No Enterprise Bloat**
   - Minimal dependency verification
   - Direct implementation
   - Simple abstractions

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest src/features/cks/learning/tests/

# Run specific test file
python -m pytest src/features/cks/learning/tests/test_usage_pattern_tracker.py

# Run with coverage
python -m pytest --cov=src/features/cks/learning src/features/cks/learning/tests/
```

### Test Structure

- `test_usage_pattern_tracker.py`: Usage pattern tracking tests
- `test_adaptive_optimizer.py`: Optimization engine tests
- `test_quality_scorer.py`: Quality assessment tests
- `test_evidence_learning.py`: Learning system tests
- `test_continuous_learner_integration.py`: Integration tests

## Performance Characteristics

### Algorithm Complexity
- **Pattern Tracking**: O(1) per operation, O(n log n) for analysis
- **Quality Scoring**: O(n) for evidence processing
- **Optimization**: O(n log n) for insight generation
- **Memory Usage**: O(n) with configurable limits

### Resource Management
- Bounded operation history with configurable window size
- Automatic cleanup of expired insights
- Efficient database operations with SQLite
- Thread-safe concurrent operations

## Database Schema

### Tables

1. **usage_patterns**: Usage pattern data
2. **operation_history**: Raw operation records
3. **quality_metrics**: Knowledge quality scores
4. **quality_evidence**: Quality assessment evidence
5. **learning_insights**: Generated learning insights
6. **learning_history**: Learning cycle records

## Integration Examples

### CSF Integration

```python
# Automatic CSF configuration integration
from cks.learning import ContinuousLearner

# Uses CSF config if available
learner = ContinuousLearner()
```

### Custom Evidence Sources

```python
# Custom quality evidence
custom_evidence = [
    {"type": "custom_metric", "value": 0.85, "data": {"source": "custom_system"}},
    {"type": "peer_review", "value": 0.9, "data": {"reviewers": 3}}
]
metrics = learner.assess_quality("custom_knowledge", custom_evidence)
```

### Batch Operations

```python
# Batch usage tracking
operations = [
    ("component1", "op1", 0.5, True),
    ("component2", "op2", 1.0, False),
    # ... more operations
]

for component, operation, duration, success in operations:
    learner.track_usage(component, operation, duration, success)
```

## Monitoring and Debugging

### System Status

```python
status = learner.get_system_status()

# Component details
patterns_count = status['components']['pattern_tracker']['patterns_tracked']
quality_count = status['components']['quality_scorer']['knowledge_assessed']
insights_count = status['components']['evidence_learning']['insights_generated']

# Health check
health_status = status['health']['status']
last_update = status['health']['last_update']
```

### Logging Configuration

```python
import logging

# Enable debug logging
logging.getLogger('cks.learning').setLevel(logging.DEBUG)

# Log to file
file_handler = logging.FileHandler('learning.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logging.getLogger('cks.learning').addHandler(file_handler)
```

## Best Practices

### Performance Optimization
1. Configure appropriate `pattern_window_size` for your use case
2. Enable auto-optimization only in production environments
3. Set reasonable `confidence_threshold` to avoid false positives
4. Use batch operations where possible

### Quality Assurance
1. Always provide evidence for quality assessments
2. Monitor system health and performance metrics
3. Regularly review optimization insights
4. Validate constitutional compliance periodically

### Resource Management
1. Set appropriate limits (`max_insights_retained`, `pattern_window_size`)
2. Enable automatic cleanup (`backup_enabled`, `cleanup_interval`)
3. Monitor database size and performance
4. Use context managers for resource cleanup

## Troubleshooting

### Common Issues

1. **High Memory Usage**: Reduce `pattern_window_size` and `max_insights_retained`
2. **Slow Performance**: Enable database cleanup and reduce analysis frequency
3. **Database Locks**: Ensure proper shutdown with `learner.shutdown()`
4. **Missing Insights**: Check `confidence_threshold` and enable auto-optimization

### Debug Information

```python
# Enable debug mode
import logging
logging.basicConfig(level=logging.DEBUG)

# Check system status
status = learner.get_system_status()
print(json.dumps(status, indent=2))
```

## License and Compliance

This framework is developed under CSF constitutional requirements with:
- Solo developer optimization
- Evidence-based implementation methodology
- Force multiplier integration capabilities
- No enterprise bloat design principles

Full compliance validation is included through the integrated validation system.
