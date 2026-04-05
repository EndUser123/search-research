# Enhanced Anti-Deception Architecture Test Suite

Comprehensive test suite for validating the Enhanced Anti-Deception Architecture
implemented across Claude Code hooks.

## 🏗️ Test Structure

```
anti_deception_enhanced/
├── unit_tests/           # Individual component validation
│   └── test_post_tool_use_validation.py
│   └── test_llm_supervisor.py
├── integration_tests/    # Cross-component communication
│   └── test_cross_hook_communication.py
├── performance_tests/    # Sub-2 second validation overhead
│   └── test_validation_overhead.py
├── scenario_tests/       # Real-world workflow validation
│   └── test_real_world_workflows.py
├── test_utils/           # Test runner and utilities
│   └── test_runner.py
├── run_tests.py          # Quick test runner
└── README.md            # This file
```

## 🎯 Test Categories

### Unit Tests
Validate individual components in isolation:
- **PostToolUse BalancedValidationLogic**: Core validation decision making
- **LLM Supervisor**: Hybrid validation with cost optimization
- **Evidence Repository**: Storage and retrieval operations
- **Validation Engines**: Parallel execution performance

### Integration Tests
Validate cross-component interactions:
- **Cross-Hook Communication**: Event passing between hooks
- **Evidence Aggregation**: Collection across hook lifecycle
- **Session Management**: Multi-hook coordination
- **Error Propagation**: Handling between components

### Performance Tests
Validate performance requirements:
- **Sub-2 Second Overhead**: Maximum validation time
- **Memory Usage**: < 100MB additional overhead
- **Parallel Processing**: < 0.5s execution time
- **Cache Performance**: > 85% hit rate
- **Concurrent Load**: Performance under stress

### Scenario Tests
Validate real-world development workflows:
- **Code Editing**: Safe function modifications and risky architecture changes
- **File Operations**: Safe creation vs dangerous modifications
- **Testing Workflows**: Test execution with evidence collection
- **Deployment Scenarios**: Production deployments and emergency rollbacks

## 🚀 Running Tests

### Quick Start
```bash
# Run all tests
python run_tests.py

# Run specific suite
python run_tests.py --suite unit
python run_tests.py --suite integration
python run_tests.py --suite performance
python run_tests.py --suite scenario

# Generate detailed JSON report
python run_tests.py --json-report test_results.json

# Validate performance requirements
python run_tests.py --validate-performance
```

### Advanced Usage
```bash
# Run with pytest directly
python -m pytest unit_tests/ -v
python -m pytest integration_tests/ -v
python -m pytest performance_tests/ -v
python -m pytest scenario_tests/ -v

# Run with coverage
python -m pytest --cov=../.claude/hooks --cov-report=html

# Run performance tests specifically
python -m pytest performance_tests/ -v -k "performance"
```

## 📊 Performance Requirements

The Enhanced Anti-Deception Architecture must meet these performance criteria:

| Metric | Requirement | Target |
|--------|-------------|--------|
| Validation Overhead | Maximum time per validation | < 2 seconds |
| Memory Usage | Additional memory overhead | < 100MB |
| Parallel Processing | Concurrent validation time | < 0.5s |
| Cache Hit Rate | Validation cache effectiveness | > 85% |
| Concurrent Load | 20+ concurrent validations | < 3s total |

## 🧪 Test Results Interpretation

### Success Criteria
- ✅ **All tests pass**: Architecture is working correctly
- ⚠️ **Performance warnings**: Acceptable but could be optimized
- ❌ **Failures**: Critical issues that must be addressed

### Performance Validation
The test suite validates:
- Individual validation timing
- Parallel execution efficiency
- Memory usage patterns
- Cache hit rates
- Concurrent processing capability

### Evidence Validation
Tests verify that:
- Evidence is properly collected for all operations
- Cross-hook communication works correctly
- Session evidence is complete
- Validation decisions are properly documented

## 🔧 Configuration

### Environment Variables
```bash
# Test configuration
ANTI_DECEPTION_TEST_LEVEL=standard  # basic|standard|high_security
ANTI_DECEPTION_CACHE_SIZE=1000     # Cache entries
ANTI_DECEPTION_TIMEOUT=30          # Test timeout (seconds)
```

### Test Data
Tests use mock data and don't require:
- Real LLM API calls
- Actual file system modifications
- Network access
- External dependencies

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all components are properly installed
   ```bash
   # Check component availability
   python -c "from post_tool_use import BalancedValidationLogic; print('OK')"
   python -c "from llm_supervisor import LLMSupervisor; print('OK')"
   ```

2. **Performance Test Failures**: Check system resources
   ```bash
   # Monitor resource usage
   python run_tests.py --suite performance --validate-performance
   ```

3. **Test Timeouts**: Increase timeout for slow systems
   ```bash
   export ANTI_DECEPTION_TIMEOUT=60
   python run_tests.py
   ```

### Debug Mode
Run tests with extra debugging:
```bash
python -m pytest -v -s --tb=long unit_tests/
```

## 📈 Continuous Integration

### GitHub Actions Example
```yaml
name: Enhanced Anti-Deception Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Tests
        run: |
          python tests/anti_deception_enhanced/run_tests.py \
            --json-report test_results.json \
            --validate-performance
      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_results.json
```

## 🤝 Contributing

### Adding New Tests
1. Place in appropriate test category directory
2. Follow existing naming conventions
3. Include performance assertions where relevant
4. Add proper documentation and comments

### Test Structure Template
```python
class TestNewComponent:
    """Test new component functionality."""

    @pytest.fixture
    def component(self):
        """Create component instance for testing."""
        return NewComponent()

    @pytest.mark.asyncio
    async def test_core_functionality(self, component):
        """Test core component functionality."""
        # Test implementation
        assert result.is_valid is True

    def test_performance_requirements(self, component):
        """Test performance requirements."""
        start_time = time.time()
        # Execute test
        execution_time = time.time() - start_time
        assert execution_time < 2.0  # Sub-2 second requirement
```

## 📚 Additional Resources

- [Enhanced Anti-Deception Architecture Documentation](../docs/architecture.md)
- [Performance Guidelines](../docs/performance.md)
- [API Reference](../docs/api.md)
- [Troubleshooting Guide](../docs/troubleshooting.md)

## 📄 License

This test suite is part of the Enhanced Anti-Deception Architecture project
and follows the same licensing terms.
