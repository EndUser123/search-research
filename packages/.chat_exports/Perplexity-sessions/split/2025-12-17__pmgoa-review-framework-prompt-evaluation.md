---
title: "PMGOA Review Framework Prompt Evaluation"
date: "2025-12-17"
mode: "COPILOT"
uuid: "268f86a0-3ed3-4770-9c27-0039a5facf28"
entry_count: 1
---

## Human

Do you see anything to improve in this prompt?

# PMGOA Review Framework
*Pre-Mortem • Gaps • Opportunities • Outstanding Outcomes*


## Usage Modes


**🚀 Quick Review** (5-10 min): Phases 1-2 + core questions
**📋 Standard Review** (15-20 min): All phases, simplified format
**🔬 Deep Dive** (30+ min): Full framework with detailed analysis


## Context Adaptation


**Web/Mobile Apps**: Emphasize UX, accessibility, and performance metrics
**APIs/Services**: Focus on contracts, scalability, and monitoring
**Data Science/ML**: Prioritize validation, bias, and deployment considerations
**Infrastructure**: Highlight reliability, security, and operational aspects


## Systematic Review Framework


### Phase 1: Risk & Failure Analysis
**🔍 Pre-Mortem**  
What are the top 3 failure scenarios? Consider likelihood and impact of each.


**🔄 Second-Order Effects**  
What unintended consequences or ripple effects might occur? Consider downstream impacts.


### Phase 2: Completeness & Coverage
**❓ Gaps**  
What's missing or incomplete? Any overlooked requirements or dependencies?


**🎯 Pareto Principle (80/20)**  
Where can you focus effort for maximum impact? Which areas deliver disproportionate value?


### Phase 3: Optimization & Value
**💡 Opportunities**
What are the top 3 bottlenecks or pain points? What's one change that could 2x the value or halve the effort?


**😊 Happy Path Optimization**
What's the step-by-step flow for the primary successful use case? Are there any unnecessary friction points or complexity?


**⭐ Outstanding Outcomes**
What measurable results will make this truly exceptional?


### Phase 4: Constraints & Trade-offs
**⚖️ Iron Triangle Trade-offs**  
How do time, cost, and quality/scope interact? What constraints exist in this relationship?


**💰 Technical Debt Assessment**  
What's the balance between short-term delivery and long-term maintainability?


### Phase 5: Mental Models & Bias
**🧠 Cognitive Biases Check**  
What mental shortcuts might be misleading the analysis? Watch for survivorship bias and availability heuristics.


## Quick Reflection Questions
- Did you forget something critical?
- Any predictable issues on the horizon?
- Is this really the best approach available?


## Response Guidelines for AI Assistant


**Adapt format based on usage mode:**


**🚀 Quick Review Response:**
- Top 3-5 priority issues with brief rationale
- Immediate next steps only


**📋 Standard Review Response:**
- Prioritized checklist (High/Medium/Low)
- Key recommendations with implementation effort (Easy/Medium/Hard)


**🔬 Deep Dive Response:**
- Full analysis with risk scoring (1-5 scale for likelihood × impact)
- Timeline categorization (Immediate/Future/Strategic)
- Confidence levels for each assessment
- Alternative approaches with trade-off analysis


**Always include:**
- **Actionable Recommendations**: Specific, implementable steps
- **Rationale**: Why each issue matters and potential impact


*Tailor depth to project context and user needs. Focus on highest-leverage insights first.*

## Assistant

## PMGOA Prompt: Comprehensive Improvement Analysis

Your prompt is **thoughtfully structured and immediately useful**, with strong conceptual foundations. Here are the strategic improvements organized by impact level:

### **High-Impact Improvements**

**1. Add explicit validation layer for context comprehension**

The framework assumes the assistant understands the submission's domain (web app vs. ML model, etc.) but doesn't require confirmation. Add:

> **Pre-Flight Check (NEW)**  
> Confirm context-specific interpretation: "This review applies to [domain]. Does the user need me to validate or adjust scope before proceeding?"

**Rationale**: Prevents misdirected analysis. For a technical debt assessment on an API, emphasizing UX accessibility wastes cognitive cycles.

**2. Introduce explicit confidence/uncertainty quantification**

Your Deep Dive response guidelines include risk scoring but not **confidence levels in the assessment itself**. Add:

> **Assessment Confidence**  
> Mark each finding: High (>80% confident), Medium (50-80%), Low (<50%)
> 
> Include brief reasoning when confidence is below Medium.

**Rationale**: Prevents false precision. A deep dive with unqualified claims carries unwarranted authority.[1]

**3. Add dependency mapping for Multi-layered systems**

Phases handle individual concerns well, but miss **cross-phase dependencies**. Example: A Phase 1 risk might create Phase 3 opportunities. Add:

> **Cross-Phase Dependency Check**  
> Which risks create opportunities? Which opportunities introduce new gaps?

**Rationale**: Avoids siloed analysis; captures second-order insights more systematically.

***

### **Medium-Impact Improvements**

**4. Quantify the "2x value / halve effort" claim in Phase 3**

"What's one change that could 2x the value or halve the effort?" is aspirational but vague. Specify:

> **Before proposing opportunities**: Establish baseline metrics
> - Current delivery timeline
> - Key value drivers (e.g., user acquisition, system reliability, development velocity)
> - Bottleneck severity (qualitative: Minor/Moderate/Critical)

**Rationale**: Makes "2x" claims testable and prevents unfounded optimization suggestions.[1]

**5. Add an explicit "Constraints Catalog" upfront**

Phase 4 asks about Iron Triangle trade-offs, but you don't require users to articulate constraints beforehand. Add to Context Adaptation:

> **Constraint Declaration** (required for all modes)  
> - Hard constraints: Non-negotiable scope, timeline, budget, or dependencies  
> - Soft constraints: Preferences with flexibility  
> - External dependencies: Teams, systems, vendors you can't control

**Rationale**: Prevents recommending infeasible changes. Constraints shape everything downstream.[2][3]

**6. Clarify "Outstanding Outcomes" success criteria**

The current phrasing ("measurable results that will make this exceptional") is itself vague. Specify:

> **Outstanding Outcomes must:**
> - Reference a baseline or comparable benchmark
> - Include specific metric, target value, and measurement method
> - Example: "Reduce P99 latency from 500ms to <200ms, measured via production APM"

**Rationale**: Prevents aspirational fluff; ensures outcomes are actionable.

***

### **Lower-Impact But Useful Additions**

**7. Add a "Blind Spot" bias section**

Your cognitive biases check mentions survivorship bias and availability heuristics, but misses industry-specific blinds. Add:

> **Domain-Specific Blind Spots** (context-adaptive)  
> - **Web/Mobile**: Underestimating async/network edge cases  
> - **ML**: Assuming training data distributions match production  
> - **Infrastructure**: Missing cascading failure modes  
> - **APIs**: Backwards compatibility and deprecation paths

**Rationale**: Makes bias detection actionable, not theoretical.[4]

**8. Introduce a "Time Decay" dimension**

Your phases are conceptually organized but don't distinguish **urgency tiers**. Phases already mention "Timeline categorization" in Deep Dive guidelines, but expand:

> **Urgency Tiers for Recommendations:**  
> - **This sprint**: Blocks active work or introduces critical risk  
> - **Next quarter**: Improves velocity or prevents scaling issues  
> - **Strategic**: Shapes architecture for future capability

**Rationale**: Helps users prioritize amidst competing demands; reduces analysis paralysis.[2]

**9. Add a feedback loop mechanism**

The framework is one-directional (prompt → response). For iterative use, add:

> **Post-Review Actions** (new closing section)  
> 1. Which recommendation will you implement first?  
> 2. How will you measure its impact?  
> 3. Schedule a follow-up review after implementation (suggest timeline)

**Rationale**: Turns one-time analysis into continuous improvement practice.

***

### **Structural Refinements**

**10. Reorder "Constraints & Trade-offs" to Phase 2**

Currently Phase 4, constraints should inform gap analysis and opportunity prioritization. Move it earlier and make it **prerequisite knowledge** for other phases.

**11. Clarify the Phases as "Analysis Lenses" not "Sequential Steps"**

Users may interpret Phases 1-5 as sequential, creating artificial ordering. Clarify:

> **Framework Structure:**  
> These five perspectives can be explored in any order. Choose the sequence based on your project's maturity and primary concerns.

**Rationale**: Prevents rigidity; acknowledges that an early-stage feature might skip Phase 4 but prioritize Phase 1.

***

### **Summary of Recommendations**

| **Improvement** | **Effort** | **Impact** | **Priority** |
|---|---|---|---|
| Add validation layer for context | Easy | High | 1 |
| Introduce confidence quantification | Easy | High | 2 |
| Require constraint declaration | Medium | High | 3 |
| Clarify "Outstanding Outcomes" criteria | Easy | Medium | 4 |
| Add domain-specific blind spots | Medium | Medium | 5 |
| Quantify bottleneck severity upfront | Medium | Medium | 6 |
| Add feedback loop mechanism | Easy | Medium | 7 |
| Clarify Phases as non-sequential | Easy | Low | 8 |

The prompt's **core value is its multi-lens architecture**—combining pre-mortem thinking with value optimization. The improvements above tighten execution by reducing ambiguity and adding feedback cycles. Your framework would scale particularly well for technical projects where confidence levels and constraint mapping are critical.[2]
