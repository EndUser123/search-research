---
name: "/speckit.execute"
category: "Speckit Workflow"
purpose: "Execute the implementation workflow using v6 Flow Orchestrator with real FeatureLoopEngine and TrustValidationEngine integration"
entry_point: "primary"
---

# Speckit Execute - v6 Flow Orchestrator Integration

Execute the complete speckit development pipeline from constitution through final DUF5 validation using the v6 Flow Orchestrator with real-time trust scoring, evidence collection, and specialist coordination.

## 🚀 Quick Start

### Execute with Default Settings
```bash
cd "C:\_Python\_Projects\.speckit"
python scripts/speckit_execute.py --feature-dir /path/to/feature
```

### Execute with Custom Trust Thresholds
```bash
cd "C:\_Python\_Projects\.speckit"
python scripts/speckit_execute.py --feature-dir /path/to/feature --trust-threshold 0.7 --constitution-threshold 0.8
```

### Execute in Orchestrated Mode (Recommended)
```bash
cd "C:\_Python\_Projects\.speckit"
python scripts/speckit_execute.py --feature-dir /path/to/feature --mode orchestrated --max-concurrent-systems 4
```

## ⚙️ Command Options

| Option | Default | Description |
|--------|---------|-------------|
| `--engine` | `dev6` | Engine to use (v6 Flow Orchestrator) |
| `--feature-dir` | Required | Path to feature directory for execution |
| `--feature-name` | Auto-derived | Feature name (derived from directory if not provided) |
| `--mode` | `orchestrated` | v6 execution mode: `sequential`, `feedback_driven`, `orchestrated` |
| `--trust-threshold` | `0.65` | Minimum trust score for gates |
| `--constitution-threshold` | `0.75` | Constitution gate minimum score |
| `--implementation-threshold` | `0.65` | Implementation gate minimum score |
| `--final-threshold` | `0.75` | Final gate minimum score |
| `--max-feedback-loops` | `3` | Maximum feedback loops for correction attempts |
| `--tdd-strategy` | `single_wave` | TDD strategy: `single_wave`, `sequential_waves`, `parallel_stages` |
| `--max-tdd-waves` | `3` | Maximum TDD waves for sequential_waves strategy |
| `--save-evidence` | `True` | Save evidence files to .taskmaster/evidence/ |
| `--constitution-validate` | `True` | Run constitution gate validation |
| `--enable-specialist-coordination` | `True` | Enable CSF NIP specialist coordination |
| `--enable-security-validation` | `True` | Enable security validation and threat modeling |
| `--timeout-seconds` | `3600` | Execution timeout in seconds (default: 1 hour) |
| `--max-concurrent-systems` | `4` | Maximum concurrent systems for orchestrated mode |

## 📋 Use Cases

### When to Use /speckit.execute

- **Complete Feature Development**: Execute entire speckit pipeline from start to finish
- **Production Readiness Validation**: Run full v6 Flow Orchestrator with trust gates and evidence collection
- **Complex Feature Implementation**: Handle multi-component features requiring specialist coordination
- **Quality Assurance**: Execute with comprehensive validation, security checks, and constitution compliance
- **Continuous Integration**: Automated pipeline execution with configurable trust thresholds

### When NOT to Use /speckit.execute

- **Simple Tasks**: Use individual speckit commands for single-phase work
- **Testing Only**: Use `/speckit.checklist` for validation-only workflows
- **Research Phase**: Use `/speckit.research` for investigation and discovery
- **Planning Only**: Use `/speckit.plan` for design and architecture work

## 🔧 Prerequisites

### Required Components
1. **CSF NIP Framework**: v6 Flow Orchestrator must be properly installed
2. **Feature Directory**: Must contain valid `spec.md`, `plan.md`, and `tasks.md` files
3. **Constitution**: Project constitution must exist in `.speckit/memory/constitution.md`
4. **Python Environment**: Python 3.8+ with required dependencies

### Validation Commands
```bash
# Check CSF NIP installation
cd "C:\_Python\_Projects\__csf.nip"
python -c "from src.modules.development_framework.v6_flow_orchestrator.flow_orchestrator import FlowOrchestrator; print('✅ v6 Flow Orchestrator available')"

# Validate feature directory structure
cd /path/to/feature
ls -la | grep -E "(spec\.md|plan\.md|tasks\.md)"
```

## 🔧 Troubleshooting

### Common Issues and Solutions

**❌ "v6 Flow Orchestrator not available"**
```bash
# Solution: Check CSF NIP installation and Python path
cd "C:\_Python\_Projects\__csf.nip"
python -c "import sys; print('\n'.join(sys.path))"
```

**❌ "Feature directory not found"**
```bash
# Solution: Verify feature directory exists and is accessible
ls -la /path/to/feature
```

**❌ "Missing required files (spec.md, plan.md, tasks.md)"**
```bash
# Solution: Run speckit planning commands first
/speckit.specify "your feature description"
/speckit.plan
/speckit.tasks
```

**❌ "Constitution gate validation failed"**
```bash
# Solution: Check project constitution and adjust thresholds
cat .speckit/memory/constitution.md
# Re-run with lower constitution threshold: --constitution-threshold 0.6
```

**❌ "Trust score below threshold"**
```bash
# Solution: Review evidence logs and adjust trust thresholds or improve implementation
ls -la .taskmaster/evidence/
# Re-run with lower trust threshold: --trust-threshold 0.5
```

### Performance Issues

**Slow Execution**
- Reduce `--max-concurrent-systems` if system resources are limited
- Use `--mode sequential` for simpler features
- Increase `--timeout-seconds` for complex features

**Memory Issues**
- Use `--max-feedback-loops 2` to limit correction attempts
- Disable optional validation with `--enable-specialist-coordination false`

## 🧠 Complete Operational Logic

The v6 Flow Orchestrator executes through these phases with real-time trust scoring:

1. **Parse Arguments**: Extract speckit execution parameters with v6 engine defaults
2. **Initialize Flow Orchestrator**: Create real v6 flow session with trust gates and evidence integration
3. **Parameter Mapping**: Convert speckit arguments to v6 FlowOrchestrator configuration
4. **Execute Real v6 Workflow**: Run actual FeatureLoopEngine with TDD cycles and TrustValidationEngine with evidence-based scoring
5. **Collect Evidence**: Gather comprehensive evidence from v6 engines with real trust scores
6. **Generate Reports**: Provide detailed execution summary with v6 evidence integration

### Trust Gate Configuration
- **Constitution Gate**: Validates against project constitution principles
- **Implementation Gate**: Checks code quality and completeness
- **Final Gate**: Validates overall feature readiness and integration

### Evidence Collection
- All execution artifacts saved to `.taskmaster/evidence/`
- Real-time trust scoring with configurable thresholds
- Specialist coordination logs and recommendations
- Security validation results and threat analysis

### Integration Points
- **CSF NIP Specialists**: Automatic coordination for security, performance, and architecture validation
- **TaskMaster Integration**: Evidence storage and retrieval through TaskMaster system
- **DUF5 Validation**: Final deployment readiness validation
- **Knowledge System**: Pattern learning and organizational knowledge integration
