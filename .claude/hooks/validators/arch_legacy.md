---



name: arch
category: command
purpose: Ultimate Architectural Advisor (ALL modes + Artifacts + CKS + Complexity + Constitution + Risk/Debt + Mental Models)
usage: /arch [question] [--zen]
dependencies:
  - P:/__csf.nip/src/csf/cli/nip/arch.md
  - P:/__csf.nip/src/lib/enhancement_router.py
  - P:/__csf.nip/src/features/lib/daemons/unified_semantic_daemon.py
  - P:/__csf.nip/src/csf/core/complexity_detector.py
  - P:/__csf.nip/src/csf/core/constitutional_tree_validator.py
  - P:/__csf.nip/src/features/rca/mental_model_selector.py
  - P:/__csf.nip/src/features/lib_solo_dev_complexity_analyzer.py
  - P:/__csf.nip/src/features/lib_adversarial_verification.py
  - P:/__csf.nip/src/features/uaf/__init__.py
  - P:/CLAUDE.md
  - P:/AGENTS.md
---

# arch

**Main Definition:** `P:/__csf.nip/src/csf/cli/nip/arch.md`

## ⚡ EXECUTION DIRECTIVE

**When invoked:**

1.  **Analyze Context:** Briefly check the user's active files.
2.  **EXECUTE** the following Python code:

```python
import sys
import os
from pathlib import Path

# Ensure correct path for imports
if "P:/" not in sys.path: sys.path.insert(0, "P:/")
if "P:/__csf/src" not in sys.path: sys.path.insert(0, "P:/__csf/src")

from csf.enhancement_router import EnhancementRouter, parse_enhancement_flags, EnhancementMode
from rca.mental_model_selector import select_mental_models, format_recommendations

# 1. CONFIGURE DEFAULTS
if "ENHANCEMENT_DEFAULT_MODE" not in os.environ:
    os.environ["ENHANCEMENT_DEFAULT_MODE"] = "all"

# 2. PROMPT COMPLEXITY
user_input = ARCHITECTURE_QUESTION
complexity_info = ""
try:
    from features.lib.complexity_detector import ComplexityDetector
    from features.lib.solo_dev_complexity_analyzer import SoloDevComplexityAnalyzer

    solo_analyzer = SoloDevComplexityAnalyzer()
    detector = ComplexityDetector()
    c_result = detector.detect_level(user_input)

    complexity_info += f"""
[DECISION LEVEL]
Level: {c_result.level.name} (Est. {c_result.estimated_duration}s)
Quality Drivers: {", ".join([f"{qa.name} ({qa.weight})" for qa in c_result.quality_tree.sorted_attributes()])}
"""

    # Add Solo-Dev specific insights
    solo_analysis = solo_analyzer.analyze_implementation(user_input)
    complexity_info += f"\n[SOLO-DEV FEASIBILITY]\nAppropriate for Solo: {'✅ Yes' if solo_analysis.solo_dev_appropriate else '⚠️ High Maintenance'}\nComplexity Score: {solo_analysis.complexity_score:.2f}\n"

    if solo_analysis.warnings:
        complexity_info += "\n[SOLO-DEV COMPLEXITY WARNINGS]\n"
        for w in solo_analysis.warnings[:3]:
            complexity_info += f"- {w.severity.value.upper()}: {w.message} (Suggestion: {w.suggestion})\n"

except Exception as e:
    complexity_info = f"\n[COMPLEXITY ANALYSIS UNAVAILABLE: {e}]\n"

# 3. MENTAL MODEL SELECTION
mental_models_context = ""
try:
    recommendations = select_mental_models(user_input, max_models=3)
    mental_models_context = f"\n\n{format_recommendations(recommendations)}"
except Exception:
    pass

# 3b. UAF: Decompose into Subagent Tasks (Unified Agent Fabric)
uaf_context = ""
try:
    from uaf import decompose_architecture
    tasks = decompose_architecture(user_input)
    uaf_context = "\n\n[UAF AGENT MISSIONS]\n"
    for t in tasks:
        uaf_context += f"- Phase: {t.task_type} | Pool: {t.pool}\n  Mission: {t.prompt}\n"
except Exception as e:
    uaf_context = f"\n\n[UAF Error] {e}"

# 4. DEPENDENCY CONTEXT (NEW!)
dependency_context = ""
try:
    # simple heuristic: find words that look like file paths or .py/.md files
    import re
    potential_files = re.findall(r'[\w/\\-]+\.[a-zA-Z]+', user_input)
    seen_deps = set()
    for fname in potential_files[:3]: # Limit to 3 files to avoid context bloat
        fpath = Path(fname) if "P:/" in fname else Path(f"P:/{fname}")
        # Try to resolve relative to current dir if needed, but here we assume absolute or generic
        if not fpath.exists():
             # Try simple search in src
             src_path = Path(f"P:/__csf/src/{fname}")
             if src_path.exists(): fpath = src_path

        if fpath.exists() and fpath.suffix in ['.py', '.ts', '.js']:
            content = fpath.read_text(encoding='utf-8')
            # Extract imports (simple regex)
            imports = re.findall(r'^(?:import|from)\s+[\w\.]+', content, re.MULTILINE)
            if imports:
                seen_deps.add(f"File: {fpath.name}")
                seen_deps.update(imports[:10]) # Limit imports per file

    if seen_deps:
        dependency_context = "\n\n[DEPENDENCY CONTEXT]\n" + "\n".join(seen_deps)
except Exception:
    pass

# 5. CONSTITUTIONAL CONTEXT
constitutional_context = ""
try:
    const_path = Path("P:/CLAUDE.md")
    if const_path.exists():
        content = const_path.read_text(encoding='utf-8')
        import re
        solo_match = re.search(r'## Solo Developer Constraints.*?(?=\n## |\Z)', content, re.DOTALL)
        if solo_match:
            constitutional_context += f"\n\n[CONSTITUTIONAL CONSTRAINTS]\n{solo_match.group(0)[:2000]}..."
except Exception:
    pass

try:
    anti_pattern_path = Path("P:/skills/solo-dev-authority/PROHIBITED_PATTERNS.md")
    if anti_pattern_path.exists():
        constitutional_context += f"\n\n[PROHIBITED PATTERNS]\n{anti_pattern_path.read_text(encoding='utf-8')[:1500]}..."
except Exception:
    pass

# 6. KNOWLEDGE (CKS + CHS + ADRs)
knowledge_context = ""

# 6a. CKS Semantic Search
try:
    from daemons.unified_semantic_daemon import SemanticClient
    client = SemanticClient(auto_start=False)
    if client.connect(timeout=2):
        results = client.search('cks', f"architecture {user_input}", limit=3)
        if results.get('results'):
             knowledge_context += "\n\n[RELEVANT CKS PATTERNS]\n"
             for r in results['results']:
                 knowledge_context += f"- {r.get('title')}: {r.get('content')[:300]}...\n"
except Exception:
    pass

# 6b. CHS (Chat History Search) - Find similar past decisions
chs_context = ""
try:
    import subprocess
    # Extract key terms for search
    search_terms = user_input[:100].replace('"', '\\"')
    result = subprocess.run(
        ["python", "-m", "chs.chat_search", "search", search_terms, "--limit", "3"],
        cwd="P:/__csf",
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0 and result.stdout.strip():
        chs_context = f"\n\n[SIMILAR PAST DECISIONS (from CHS)]\n{result.stdout[:1000]}..."
except Exception:
    pass

knowledge_context += chs_context

# 6d. Adversarial Verification (Falsification)
adversarial_context = ""
try:
    from features.lib.adversarial_verification import create_falsification_state
    # This creates a state we can use to guide the LLM's self-challenge
    _, state_dict = create_falsification_state(
        assumption=f"Architecture for {user_input[:50]}...",
        risk_type="architectural_mismatch",
        counter_searches=["contradictory evidence", "failure cases", "alternatives deemed 'impossible'"]
    )
    adversarial_context = f"\n\n[ADVERSARIAL CHALLENGE DATA]\nAssumptions to falsify: {', '.join(state_dict['assumptions'])}\nCounter-searches suggested: {', '.join(state_dict['counter_searches'])}"
except Exception as e:
    adversarial_context = f"\n\n[ADVERSARIAL CHALLENGE: {e}]\n"

knowledge_context += adversarial_context

# 6e. Historical ADRs
idx_path = Path("P:/__csf/docs/adr/index.md")
if idx_path.exists():
    knowledge_context += f"\n\n[HISTORICAL ADRs]\n{idx_path.read_text(encoding='utf-8')[:1500]}..."

# 7. PREPARE INPUT w/ ALL ARTIFACT REQUIREMENTS
context_wrapper = f"""
{user_input}
{complexity_info}
{mental_models_context}
{uaf_context}
{dependency_context}
{constitutional_context}
{knowledge_context}

================================================================================
CRITICAL PROTOCOLS (from AGENTS.md):
================================================================================
- **Deep Reasoning Required:** Use step-by-step Chain-of-Thought for complexity > Level 3.
- **Falsification:** Actively attempt to DISPROVE your best option before recommending.
- **Pre-Mortem:** Simulate a 6-month failure scenario.

================================================================================
MANDATORY OUTPUT ARTIFACTS (You MUST generate ALL of these):
================================================================================

1. [MENTAL MODEL APPLICATION]
Apply the recommended mental model(s) from the [Mental Model Selection] section above.
Show your reasoning step-by-step, strictly following the **Action** instructions provided for each selected model.

2. [PRE-MORTEM ANALYSIS]
(Even if not prompted) Imagine it is 6 months from now and this decision has FAILED.
- List the specific reasons WHY it failed.
- List the early warning signs we missed.
- Write the "Retrospective" summary of the failure.

3. [RISK MATRIX]
For each proposed option, generate a Risk Score (1-10) with justification:
| Option | Risk Score | Key Risks |
|--------|------------|-----------|
| ...    | X/10       | ...       |

4. [FORCED ALTERNATIVES]
You MUST propose at least 3 distinct approaches, even for simple questions.

5. [ROLLBACK PLAN]
For the recommended option, provide a complete rollback strategy.

6. [TECH DEBT ESTIMATION]
| Option | Coupling Impact | Maintenance Burden | Debt Score |
|--------|-----------------|-------------------|------------|
| ...    | Low/Med/High    | ...               | X/10       |

7. [TIMELINE ESTIMATION]
| Option | T-Shirt Size | Hours | Confidence |
|--------|--------------|-------|------------|
| ...    | S/M/L/XL     | X-Y   | Low/Med/High|

8. [CONSTITUTIONAL COMPLIANCE]
Validate against the [CONSTITUTIONAL CONSTRAINTS] context.

9. [AUTO-DRAFT ADR]
Generate a full Architecture Decision Record (ADR) in Markdown.

10. [CWO COGNITIVE CHECKLIST]
Generate a specific implementation checklist mapped to CWO phases.

11. [CKS KNOWLEDGE HANDOFF]
Generate a JSON-like block for CKS ingestion.

12. [CONFIDENCE CALIBRATION]
State your overall confidence in the recommendation (0-100%).
- What would INCREASE your confidence?
- What would DECREASE your confidence?
- What key assumption, if wrong, would invalidate this analysis?

13. [ADVERSARIAL CHALLENGE]
Acknowledge the [ADVERSARIAL CHALLENGE DATA].
- Attempt to DISPROVE your own recommendation.
- What evidence would make you switch to one of the [FORCED ALTERNATIVES]?
"""

# 7. EXECUTE ROUTER
router = EnhancementRouter()
modes = parse_enhancement_flags(ARGUMENTS)
if not modes: modes = parse_enhancement_flags("--all")

print(f"🔄 Running Ultimate Architectural Analysis ({len(modes)} enhancement modes)...")

try:
    results = router.route(
        original_command="/arch",
        user_input=context_wrapper,
        modes=modes,
        context={"project": "current"}
    )
except Exception as e:
    print(f"⚠️ Enhancement Warning: {e}")
```

3.  **SYNTHESIZE & PRESENT:**

    - **Verify All 13 Artifacts:** Ensure every mandatory section is present.
    - **Visual Model:** Generate **Mermaid Diagram** comparing options.
    - **Anti-Sycophancy:** Address the "Challenge" output.

4.  **Fallback:** Read `P:/__csf.nip/src/csf/cli/nip/arch.md`.
