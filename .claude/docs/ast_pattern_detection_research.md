# AST Pattern Detection & Static Analysis Research

## Executive Summary

This document catalogs AST-based pattern detection techniques for Python code quality analysis, based on research from DPy, PyExamine, Code Crafter, and Python's AST module.

**Key Finding**: Python requires different verbosity thresholds (0.67x) compared to Java due to more concise syntax.

## 1. Tool Catalog

### 1.1 DPy (Code Smells Detection Tool for Python)

**Paper**: MSR 2025 - "DPy: Code Smells Detection Tool for Python"
**Authors**: Aryan Boloori, Tushar Sharma (Dalhousie University)

**Capabilities**:
- 8 design smells (class + module level)
- 11 implementation smells
- Code quality metrics at function, module, and class levels
- Export to CSV/JSON

**Architecture**:
```
Source Code → AST Parser → Source Model Layer → Detection Layer → Output
                 ↓                     ↓
            Python ast module   Scope-based type inference
```

### 1.2 PyExamine

**Paper**: "PyExamine: A Comprehensive, Un-Opinionated Smell Detection Tool for Python"
**Author**: Antonio Martini (University of Oslo)

**Capabilities**:
- 49 distinct metrics across 3 levels:
  - 24 code-level metrics
  - 6 architectural metrics
  - 19 structural metrics
- YAML-based configuration
- Multi-tiered analysis framework

**Detection Accuracy** (validated across 7 projects):
- Code-level smells: 91.4% recall
- Structural smells: 89.3% recall
- Architectural smells: 80.6% recall

### 1.3 Code Crafter

**Author**: Ben Dichter (2024)

**Purpose**: Programmatic AST transformation for Python code

**Capabilities**:
- Find and modify lists, dictionaries, sets
- Preserves code structure via AST round-trip
- Methods mirror built-in types (append, extend, insert, etc.)

**Usage Pattern**:
```python
import code_crafter as cc

with cc.File("my_file.py") as file:
    file.find_list("my_list").append(4)
    file.find_dict("my_dict").update(key="value")
    file.find_set("my_set").add(42)
```

## 2. AST Node Type Reference

### 2.1 Core Node Hierarchy

```
ast.AST (base class)
├── Root nodes
│   ├── Module(body, type_ignores)
│   ├── Expression(body)
│   └── Interactive(body)
├── Literals
│   ├── Constant(value)
│   ├── JoinedStr(values)  # f-strings
│   └── TemplateStr(values)  # template strings (3.14+)
├── Variables
│   └── Name(id, ctx)  # ctx: Load | Store | Del
├── Statements
│   ├── FunctionDef
│   ├── ClassDef
│   ├── Return
│   ├── Assign
│   ├── For
│   ├── If
│   └── Try
├── Expressions
│   ├── BinOp(left, op, right)
│   ├── UnaryOp(op, operand)
│   ├── Compare(left, ops, comparators)
│   ├── Call(func, args, keywords)
│   └── Attribute(value, attr, ctx)
└── Pattern Matching (3.10+)
    ├── Match(subject, cases)
    ├── MatchValue(value)
    ├── MatchSequence(patterns)
    └── MatchClass(cls, patterns, kwd_attrs, kwd_patterns)
```

### 2.2 Key Attributes

All `ast.expr` and `ast.stmt` nodes have:
- `lineno`: First line number (1-indexed)
- `col_offset`: UTF-8 byte offset of first token
- `end_lineno`: Last line number
- `end_col_offset`: UTF-8 byte offset of last token

## 3. Code Smell Categories

### 3.1 Implementation Smells

| Smell | Detection Rule | AST Pattern |
|-------|---------------|-------------|
| Long Statement | >80 characters | Check statement span |
| Long Parameter List | >4 parameters | `len(args.args) > 4` |
| Long Method | >67 lines* | Calculate function body LOC |
| Complex Method | CC > 7 | Count decision points |
| Complex Conditional | >2 logical operators | Count `and`/`or` in `BoolOp` |
| Magic Number | Undefined numeric literal | `Constant(value=int) not in {0, -1, 1}` |
| Long Lambda | >80 characters | Lambda body span |
| Long Message Chain | >2 chained methods | Nested `Call` nodes |
| Empty Catch Block | Only pass/return | `ExceptHandler` body check |

*Python verbosity factor: 0.67x Java thresholds

### 3.2 Design Smells

| Smell | Detection Rule | Metric |
|-------|---------------|--------|
| Multifaceted Abstraction | NOM>3 AND LCOM≥0.8 | Cohesion analysis |
| Insufficient Modularization | NOPM>20 OR NOM>30 OR WMC>100 | Size/complexity |
| Hub-like Modularization | FAN-IN>7 AND FAN-OUT>7 | Dependency analysis |
| Broken Modularization | NOF>4 AND NOM=0 | Data without methods |
| Deep Hierarchy | DIT>6 | Inheritance depth |
| Wide Hierarchy | NC>5 | Number of children |
| Broken Hierarchy | No shared methods | Interface analysis |
| Rebellious Hierarchy | Override rejects | Method contains only pass/return/raise |

### 3.3 Architectural Smells

| Smell | Description |
|-------|-------------|
| Cyclic Dependencies | Modules form circular import chains |
| Unstable Dependencies | Module depends on unstable modules |
| Scattered Functionality | Related features dispersed |
| God Components | Component handles too many responsibilities |
| Redundant Abstractions | Unnecessary abstraction layers |
| Improper API Usage | API used incorrectly |

## 4. Implementation Patterns

### 4.1 AST Visitor Pattern

```python
import ast

class CodeSmellDetector(ast.NodeVisitor):
    def __init__(self):
        self.smells = []
        self.metrics = {}

    def visit_FunctionDef(self, node):
        # Calculate function metrics
        loc = node.end_lineno - node.lineno + 1
        if loc > 67:
            self.smells.append({
                'type': 'Long Method',
                'name': node.name,
                'line': node.lineno,
                'severity': 'warning'
            })

        # Count parameters
        param_count = len(node.args.args) + len(node.args.kwonlyargs)
        if param_count > 4:
            self.smells.append({
                'type': 'Long Parameter List',
                'name': node.name,
                'line': node.lineno,
                'count': param_count
            })

        self.generic_visit(node)

    def visit_Compare(self, node):
        # Detect complex conditionals
        if isinstance(node.test, ast.BoolOp):
            op_count = len(node.test.values) - 1
            if op_count > 2:
                self.smells.append({
                    'type': 'Complex Conditional',
                    'line': node.lineno
                })
        self.generic_visit(node)
```

### 4.2 Cyclomatic Complexity Calculation

```python
def calculate_complexity(node):
    """McCabe's Cyclomatic Complexity"""
    complexity = 1  # Base complexity

    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1

    return complexity
```

### 4.3 Dependency Analysis

```python
class DependencyAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = {}  # module -> {imported_names}
        self.references = {}  # module -> {referenced_names}

    def visit_Import(self, node):
        for alias in node.names:
            module = alias.name.split('.')[0]
            if module not in self.imports:
                self.imports[module] = set()
            self.imports[module].add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            module = node.module.split('.')[0]
            if module not in self.imports:
                self.imports[module] = set()
            for alias in node.names:
                self.imports[module].add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_Name(self, node):
        # Track name references for later dependency resolution
        if isinstance(node.ctx, ast.Load):
            # This could be a reference to an imported name
            pass
        self.generic_visit(node)
```

### 4.4 LCOM Calculation (Lack of Cohesion of Methods)

```python
def calculate_lcom(methods, attributes):
    """
    LCOM = |P| - |Q|
    where P = pairs of methods that don't share attributes
          Q = pairs of methods that do share attributes
    """
    if not methods:
        return 0

    method_attr_sets = []
    for method in methods:
        used_attrs = set()
        # Walk AST to find attribute accesses
        for node in ast.walk(method):
            if isinstance(node, ast.Attribute):
                if node.attr in attributes:
                    used_attrs.add(node.attr)
        method_attr_sets.append(used_attrs)

    p = 0  # Non-intersecting pairs
    q = 0  # Intersecting pairs

    for i in range(len(method_attr_sets)):
        for j in range(i + 1, len(method_attr_sets)):
            if method_attr_sets[i] & method_attr_sets[j]:
                q += 1
            elif method_attr_sets[i] or method_attr_sets[j]:
                p += 1

    return max(0, p - q)
```

## 5. Test Results

### 5.1 DPy Validation Results

**Subject Systems**: 4 Python projects (Codespell, Mava, Maltrail, Elevant)
**Evaluators**: 2 graduate students (inter-rater agreement κ=0.87)

| Category | Manual Instances | True Positives | False Positives | False Negatives | Precision | Recall |
|----------|-----------------|----------------|-----------------|-----------------|-----------|--------|
| Implementation Smells | 899 | 838 | 33 | 61 | 0.96 | 0.93 |
| Design Smells | 30 | 30 | 0 | 0 | 1.00 | 1.00 |
| **Total** | **929** | **868** | **33** | **61** | **0.96** | **0.93** |

### 5.2 PyExamine Survey Results

**Participants**: 7 experienced Python developers (4-13 years experience, mean: 8.43)

| Category | Mean Rating (1-4 Likert) | Std Dev |
|----------|-------------------------|---------|
| Code smell detection | 3.86 | 0.38 |
| Structural smell detection | 3.71 | 0.49 |
| Architectural smell detection | 3.43 | 0.53 |
| Overall usefulness | 3.57 | 0.53 |

### 5.3 Most Common Python Code Smells

**Study**: PyExamine analysis of 183 Python projects

| Rank | Smell | Prevalence |
|------|-------|------------|
| 1 | Feature Envy | 3.68% |
| 2 | Potential Shotgun Surgery | 1.98% |
| 3 | Too Many Branches | 1.88% |
| 4 | Potential Improper API Usage | 1.51% |
| 5 | Scattered Functionality | 1.43% |
| 6 | Unstable Dependency | 1.10% |
| 7 | Long Method | 1.05% |

## 6. Python-Specific Considerations

### 6.1 Verbosity Factor

**Finding**: Python code is approximately 0.67x as verbose as Java.

**Methodology**: Analysis of 1,226 problems from Rosetta Code
- Java average LOC: 47
- Python average LOC: 31
- Verbosity factor: 31/47 ≈ 0.67

**Implication**: Metric thresholds from Java literature should be multiplied by 0.67 for Python.

Example:
- Long method threshold: Java 100 lines → Python 67 lines
- Long class threshold: Java 1000 lines → Python 670 lines

### 6.2 Python-OOP Usage

**Finding from DPy**: OOP features are used significantly in Python.

Analysis of top 10 Python repositories (Numpy, Pandas, nltk, PyTorch, Django):
- Average modules per project: 1,411
- Average classes per project: 3,835
- Classes with DIT ≥ 1: 42%
- Classes with DIT ≥ 2: 17%

**Conclusion**: Hierarchy smells remain relevant for Python analysis.

### 6.3 Type Inference Challenges

Python's dynamic typing makes type inference difficult. Solutions:

1. **Scope-based inference**: Track variable assignments within scopes
2. **Import analysis**: Use import statements to infer module/function types
3. **Type hint utilization**: Leverage PEP 484 annotations when available

## 7. Implementation Checklist

When implementing an AST-based pattern detector:

- [ ] Use `ast.NodeVisitor` for read-only analysis
- [ ] Use `ast.NodeTransformer` for code modification
- [ ] Apply Python verbosity factor (0.67) to thresholds
- [ ] Handle `async` variants (AsyncFunctionDef, AsyncFor, AsyncWith)
- [ ] Support pattern matching nodes (Python 3.10+)
- [ ] Handle type annotations (PEP 484, 526)
- [ ] Consider f-strings (JoinedStr) and template strings (TemplateStr)
- [ ] Track source locations (lineno, col_offset, end_lineno, end_col_offset)
- [ ] Implement scope-based type inference for Python
- [ ] Support both class and module level design smells

## References

1. Boloori, A., & Sharma, T. (2025). DPy: Code Smells Detection Tool for Python. MSR 2025. https://doi.org/10.5281/zenodo.14279535

2. Martini, A. (2025). PyExamine: A Comprehensive, Un-Opinionated Smell Detection Tool for Python. arXiv:2501.18327v1.

3. Python 3.14.3 Documentation. ast — Abstract syntax trees. https://docs.python.org/3/library/ast.html

4. Dichter, B. (2024). Code Crafter: Python AST transformations. https://bendichter.com/posts/2024-03-31-code-crafter

---

**Document Version**: 1.0
**Last Updated**: 2025-02-05
**Research Coverage**: DPy, PyExamine, Code Crafter, Python AST docs
