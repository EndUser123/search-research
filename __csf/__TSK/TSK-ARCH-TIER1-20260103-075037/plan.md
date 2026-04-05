# Tier 1 Architecture Frameworks - Implementation Plan

**TSK ID:** TSK-ARCH-TIER1-20260103-075037
**Created:** 2026-01-03T07:50:37Z
**Status:** Active
**Version:** 1.0

---

## Overview

This plan breaks down the Tier 1 implementation into granular, executable tasks with clear acceptance criteria for each component.

**Total Estimated Effort:** 20-24 hours
**Target Completion:** 2-4 weeks
**Approach:** Measure → Validate → Decide on Tier 2+

---

## Week 1: Foundation (12-14 hours)

### Day 1-2: Complexity Detector (3-4 hours)

#### Task 1.1: Create module structure (30 min)
```python
# File: P:/__csf.nip/src/lib/complexity_detector.py

from dataclasses import dataclass
from typing import List
from enum import Enum

class ComplexityLevel(Enum):
    LEVEL_1 = 1  # Simple decision (should we X?)
    LEVEL_2 = 2  # Architecture design
    LEVEL_3 = 3  # System-wide redesign
    LEVEL_4 = 4  # Compare alternatives

@dataclass
class QualityAttribute:
    name: str
    weight: float
    reason: str

@dataclass
class UtilityTree:
    attributes: List[QualityAttribute]

    def sorted_attributes(self) -> List[QualityAttribute]:
        return sorted(self.attributes, key=lambda x: x.weight, reverse=True)

@dataclass
class ComplexityResult:
    level: ComplexityLevel
    frameworks: List[str]
    estimated_duration: int  # seconds
    reason: str
    quality_tree: UtilityTree
```

**Acceptance:** Module compiles, all imports resolve

---

#### Task 1.2: Implement signal pattern detection (1.5h)
```python
class ComplexityDetector:
    # Signal patterns for each level
    LEVEL_SIGNALS = {
        1: [
            "should we", "should i", "use X?", "versus", "vs",
            "which one", "choose between", "better to"
        ],
        2: [
            "design", "architecture", "api", "layer", "component",
            "extract", "separate", "module"
        ],
        3: [
            "redesign", "system-wide", "migration", "refactor all",
            "complete overhaul", "platform"
        ],
        4: [
            "compare", "tournament", "evaluate options",
            "analyze alternatives", "decision matrix"
        ]
    }

    def detect_level(self, prompt: str) -> ComplexityResult:
        """
        Detect complexity level from prompt patterns.

        Returns:
            ComplexityResult with detected level and rationale
        """
        prompt_lower = prompt.lower()

        # Check patterns in reverse order (highest level first)
        for level in sorted(self.LEVEL_SIGNALS.keys(), reverse=True):
            signals = self.LEVEL_SIGNALS[level]
            if any(signal in prompt_lower for signal in signals):
                return self._create_result(level, prompt_lower)

        # Default to LEVEL 1 if no signals detected
        return self._create_result(1, prompt_lower)
```

**Acceptance:** Detects correct level on 20 test prompts (>85% accuracy)

---

#### Task 1.3: Implement quality attribute extraction (1.5h)
```python
class ComplexityDetector:
    QUALITY_PATTERNS = {
        "maintainability": {
            "keywords": ["solo dev", "solo developer", "individual", "small team",
                        "changing requirements", "evolving", "iterate quickly"],
            "default_weight": 0.8,
            "solo_boost": 1.0  # Boost to 1.0 for solo dev context
        },
        "performance": {
            "keywords": ["performance", "latency", "throughput", "speed",
                        "fast", "slow", "optimize", "response time"],
            "default_weight": 0.9
        },
        "security": {
            "keywords": ["security", "secure", "authentication", "authorization",
                        "compliance", "gdpr", "privacy", "encryption"],
            "default_weight": 0.9
        },
        "scalability": {
            "keywords": ["scale", "scalable", "users", "concurrent", "high load",
                        "growth", "millions", "thousands of users"],
            "default_weight": 0.8
        },
        "availability": {
            "keywords": ["uptime", "available", "reliable", "99.9", "sla",
                        "downtime", "fault tolerant"],
            "default_weight": 0.8
        },
        "cost": {
            "keywords": ["cost", "budget", "cheap", "expensive", "free tier",
                        "cloud costs", "billing"],
            "default_weight": 0.6
        }
    }

    def extract_quality_attributes(self, prompt: str) -> UtilityTree:
        """
        Extract quality attributes with weights from prompt.

        Returns:
            UtilityTree with detected attributes sorted by weight
        """
        prompt_lower = prompt.lower()
        attributes = []

        for attr_name, config in self.QUALITY_PATTERNS.items():
            if any(kw in prompt_lower for kw in config["keywords"]):
                weight = config["default_weight"]

                # Special handling for solo dev
                if attr_name == "maintainability":
                    if any(kw in prompt_lower for kw in ["solo dev", "solo developer", "individual"]):
                        weight = config["solo_boost"]

                attributes.append(QualityAttribute(
                    name=attr_name,
                    weight=weight,
                    reason=f"Detected from keywords: {config['keywords'][0]}"
                ))

        # Always include maintainability for solo dev if nothing else detected
        if not attributes:
            attributes.append(QualityAttribute(
                name="maintainability",
                weight=0.7,
                reason="Default for solo developer context"
            ))

        return UtilityTree(attributes=attributes)
```

**Acceptance:** Correctly extracts attributes from test prompts

---

### Day 2-3: ADR Formatter (6-8 hours)

#### Task 2.1: Create module structure (30 min)
```python
# File: P:/__csf.nip/src/lib/adr_formatter.py

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import re

@dataclass
class ADRContent:
    id: str
    title: str
    status: str
    context: str
    decision: str
    rationale: str
    confidence_score: int
    quality_attributes: List[tuple]  # (name, weight)
    positive_outcomes: List[str]
    tradeoffs: List[str]
    risks: List[str]

class ADRFormatter:
    ADR_DIR = Path("P:/__csf.nip/adr")
    TEMPLATE_PATH = Path("P:/__csf.nip/src/config/adr_template.md")

    def __init__(self):
        self.ADR_DIR.mkdir(parents=True, exist_ok=True)
        self._ensure_index()

    def _get_next_adr_id(self) -> str:
        """Get next sequential ADR ID."""
        existing = list(self.ADR_DIR.glob("ADR-*.md"))
        if not existing:
            return "0001"

        max_id = max(
            int(f.stem.split("-")[1])
            for f in existing
            if f.stem.split("-")[1].isdigit()
        )
        return f"{max_id + 1:04d}"
```

**Acceptance:** Module compiles, ADR directory created

---

#### Task 2.2: Implement ADR generation (3h)
```python
class ADRFormatter:
    TIER1_TYREE_AKERMAN_TEMPLATE = """# ADR-{id}: {title}

## Status
{status}

## Date
{date}

## Context
{context}

### Quality Attributes (Priority Order)
{quality_attributes}

## Decision
{decision}

## Rationale
{rationale}

**Confidence Score:** {confidence}%

## Consequences

### Positive Outcomes
{positive_outcomes}

### Trade-offs & Constraints
{tradeoffs}

### Risks & Mitigations
{risks}

---

*Generated by Tier 1 Architecture Frameworks*
*Date: {timestamp}*
"""

    def generate_from_analysis(
        self,
        prompt: str,
        analysis_result: dict,
        quality_attributes: UtilityTree,
        debate_results: Optional[dict] = None,
        risk_analysis: Optional[dict] = None
    ) -> ADRContent:
        """
        Generate ADR content from analysis results.

        Args:
            prompt: Original user prompt
            analysis_result: Results from architecture specialists
            quality_attributes: Extracted quality attributes
            debate_results: Optional debate council output
            risk_analysis: Optional risk assessment

        Returns:
            ADRContent object ready for saving
        """
        adr_id = self._get_next_adr_id()
        title = self._slugify_title(prompt)

        # Extract key components from analysis
        decision = self._extract_decision(analysis_result)
        rationale = self._extract_rationale(debate_results, analysis_result)

        # Calculate confidence score
        confidence = self._calculate_confidence(
            analysis_result, debate_results, risk_analysis
        )

        # Format quality attributes
        qa_formatted = self._format_quality_attributes(quality_attributes)

        return ADRContent(
            id=adr_id,
            title=title,
            status="Decided",
            context=self._format_context(prompt),
            decision=decision,
            rationale=rationale,
            confidence_score=confidence,
            quality_attributes=qa_formatted,
            positive_outcomes=self._extract_positive_outcomes(analysis_result),
            tradeoffs=self._extract_tradeoffs(analysis_result, debate_results),
            risks=self._extract_risks(risk_analysis)
        )
```

**Acceptance:** Generates valid ADR content from test data

---

#### Task 2.3: Implement file saving with Windows path handling (2h)
```python
class ADRFormatter:
    def save_adr(self, adr_content: ADRContent) -> str:
        """
        Save ADR to file with Windows-safe path handling.

        Args:
            adr_content: ADRContent to save

        Returns:
            Absolute path to saved file (with forward slashes)
        """
        filename = f"ADR-{adr_content.id}-{adr_content.title}.md"
        filepath = self.ADR_DIR / filename

        # Use forward slashes for path string
        filepath_str = str(filepath).replace("\\", "/")

        # Write content
        content = self._render_template(adr_content)
        filepath.write_text(content, encoding="utf-8")

        # Update index
        self._update_index(adr_content, filepath_str)

        return filepath_str

    def _slugify_title(self, title: str) -> str:
        """Convert title to URL-safe slug."""
        # Remove special chars, replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug[:50]  # Limit length

    def _ensure_index(self):
        """Create ADR index if it doesn't exist."""
        index_path = self.ADR_DIR / "index.md"
        if not index_path.exists():
            index_path.write_text("# Architecture Decision Records\n\n", encoding="utf-8")

    def _update_index(self, adr_content: ADRContent, filepath: str):
        """Add ADR to index."""
        index_path = self.ADR_DIR / "index.md"
        index_content = index_path.read_text(encoding="utf-8")

        entry = f"- [{adr_content.id}: {adr_content.title}]({filepath}) - {adr_content.status}\n"

        # Insert after header
        lines = index_content.split("\n")
        if len(lines) <= 2:
            index_content += "\n" + entry
        else:
            lines.insert(2, entry)
            index_content = "\n".join(lines)

        index_path.write_text(index_content, encoding="utf-8")
```

**Acceptance:** ADR files created with correct paths, index updated

---

### Day 3-4: Quality Utility Tree (3-4 hours)

#### Task 3.1: Create module structure (30 min)
```python
# File: P:/__csf.nip/src/lib/utility_tree_extractor.py

from dataclasses import dataclass
from typing import List, Dict
from complexity_detector import UtilityTree, QualityAttribute

class UtilityTreeBuilder:
    """
    Builds quality attribute utility trees for architecture decisions.

    Based on ATAM (Architecture Tradeoff Analysis Method) utility tree concept.
    """

    # Patterns for detecting quality attributes
    PATTERNS = {
        "maintainability": {
            "keywords": ["solo dev", "solo developer", "individual developer",
                        "changing requirements", "evolving needs", "iterate",
                        "quick changes", "flexible", "maintainable"],
            "default_weight": 0.8,
            "description": "Ease of modification and extension"
        },
        "performance": {
            "keywords": ["performance", "latency", "throughput", "response time",
                        "fast", "slow", "optimize", "speed"],
            "default_weight": 0.9,
            "description": "Response time and throughput"
        },
        "security": {
            "keywords": ["security", "secure", "authentication", "authorization",
                        "compliance", "gdpr", "privacy", "encrypt", "protect"],
            "default_weight": 0.9,
            "description": "Protection against threats"
        },
        "scalability": {
            "keywords": ["scale", "scalable", "growth", "concurrent users",
                        "load", "millions", "thousands"],
            "default_weight": 0.8,
            "description": "Ability to handle growth"
        },
        "availability": {
            "keywords": ["uptime", "available", "reliable", "99.9", "sla",
                        "fault tolerant", "high availability"],
            "default_weight": 0.8,
            "description": "System uptime and reliability"
        },
        "cost": {
            "keywords": ["cost", "budget", "cheap", "expensive", "free",
                        "billing", "pricing"],
            "default_weight": 0.6,
            "description": "Financial cost considerations"
        }
    }
```

**Acceptance:** Module compiles with all imports

---

#### Task 3.2: Implement extraction logic (2h)
```python
class UtilityTreeBuilder:
    def extract_from_prompt(self, prompt: str) -> UtilityTree:
        """
        Extract quality attributes from prompt.

        Args:
            prompt: User's architecture question

        Returns:
            UtilityTree with detected attributes weighted by relevance
        """
        prompt_lower = prompt.lower()
        attributes = []

        for attr_name, config in self.PATTERNS.items():
            detected_keywords = [
                kw for kw in config["keywords"]
                if kw in prompt_lower
            ]

            if detected_keywords:
                weight = self._calculate_weight(attr_name, detected_keywords, prompt_lower)
                attributes.append(QualityAttribute(
                    name=attr_name,
                    weight=weight,
                    reason=config["description"]
                ))

        # Default if nothing detected
        if not attributes:
            attributes.append(QualityAttribute(
                name="maintainability",
                weight=0.7,
                reason="Default for solo developer context"
            ))

        return UtilityTree(attributes=attributes)

    def _calculate_weight(self, attr_name: str, keywords: List[str], prompt: str) -> float:
        """Calculate weight based on keyword intensity."""
        base_weight = self.PATTERNS[attr_name]["default_weight"]

        # Boost for solo dev maintainability
        if attr_name == "maintainability":
            solo_indicators = ["solo dev", "solo developer", "individual"]
            if any(ind in prompt for ind in solo_indicators):
                return 1.0

        # Boost for emphasis words
        boost_keywords = {
            "critical": 0.1,
            "essential": 0.1,
            "must": 0.05,
            "primary": 0.05,
            "important": 0.05
        }

        for boost_word, boost_amount in boost_keywords.items():
            if boost_word in prompt:
                return min(1.0, base_weight + boost_amount)

        return base_weight
```

**Acceptance:** Extracts correct attributes from test prompts

---

#### Task 3.3: Implement specialist formatting (1h)
```python
class UtilityTreeBuilder:
    def format_for_specialists(self, tree: UtilityTree) -> str:
        """
        Format utility tree for injection into specialist prompts.

        Returns:
            Formatted string ready for prompt injection
        """
        lines = ["## Quality Attribute Priorities\n"]
        lines.append("The following quality attributes drive this decision (in priority order):\n")

        for attr in tree.sorted_attributes():
            priority = self._get_priority_label(attr.weight)
            lines.append(f"- **{attr.name}** (Weight: {attr.weight:.1f}) - {priority}")
            lines.append(f"  - {attr.reason}")

        return "\n".join(lines)

    def _get_priority_label(self, weight: float) -> str:
        """Get priority label for weight."""
        if weight >= 0.95:
            return "CRITICAL"
        elif weight >= 0.8:
            return "HIGH"
        elif weight >= 0.6:
            return "MEDIUM"
        else:
            return "LOW"
```

**Acceptance:** Output ready for specialist prompt injection

---

### Day 4: Testing & Validation (2 hours)

#### Task 4.1: Unit tests for all components (1.5h)
```python
# File: P:/__csf.nip/tests/lib/test_complexity_detector.py

import pytest
from src.lib.complexity_detector import ComplexityDetector

class TestComplexityDetector:
    def setup_method(self):
        self.detector = ComplexityDetector()

    @pytest.mark.parametrize("prompt,expected_level", [
        ("Should we use REST or GraphQL?", 1),
        ("Design a payment service API", 2),
        ("Complete system redesign for scalability", 3),
        ("Compare microservices vs monolith", 4),
        ("Use event-driven architecture for notifications?", 1),
        ("API gateway architecture design", 2),
    ])
    def test_level_detection(self, prompt, expected_level):
        result = self.detector.detect_level(prompt)
        assert result.level.value == expected_level

    def test_quality_attribute_extraction_solo_dev(self):
        prompt = "Design API for solo developer"
        result = self.detector.extract_quality_attributes(prompt)
        assert any(a.name == "maintainability" and a.weight == 1.0
                  for a in result.attributes)

    def test_quality_attribute_extraction_performance(self):
        prompt = "Design high-performance API"
        result = self.detector.extract_quality_attributes(prompt)
        assert any(a.name == "performance" and a.weight >= 0.9
                  for a in result.attributes)
```

**Acceptance:** All tests pass (>85% accuracy target)

---

#### Task 4.2: Integration test (30 min)
```python
# File: P:/__csf.nip/tests/integration/test_tier1_frameworks.py

import pytest
from src.lib.complexity_detector import ComplexityDetector
from src.lib.adr_formatter import ADRFormatter
from src.lib.utility_tree_extractor import UtilityTreeBuilder

class TestTier1Integration:
    def test_full_pipeline(self):
        """Test complete Tier 1 pipeline."""
        prompt = "Should we use REST or GraphQL for our API?"

        # Step 1: Detect complexity
        detector = ComplexityDetector()
        complexity = detector.detect_level(prompt)
        quality_attrs = detector.extract_quality_attributes(prompt)

        # Step 2: Generate ADR
        formatter = ADRFormatter()
        adr_path = formatter.save_adr(mock_analysis_result)

        # Verify
        assert complexity.level.value == 1
        assert len(quality_attrs.attributes) > 0
        assert Path(adr_path).exists()
```

**Acceptance:** Integration test passes

---

## Week 2: Enhancement & Measurement (8-10 hours)

### Day 1-2: IBIS Serializer (5-6 hours)

#### Task 5.1: Create module structure (30 min)
```python
# File: P:/__csf.nip/src/lib/ibis_serializer.py

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import json

@dataclass
class IBISArgument:
    type: str  # "pro" or "con"
    text: str
    source: str  # Which specialist/provider

@dataclass
class IBISIdea:
    id: str
    proposal: str
    provider: str
    arguments: List[IBISArgument] = field(default_factory=list)

@dataclass
class IBIS:
    issue: str
    ideas: List[IBISIdea]
    timestamp: str
    decision_id: Optional[str] = None
    recommendation: Optional[str] = None

class IBISSerializer:
    IBIS_DIR = Path("P:/__csf.nip/data/ibis")

    def __init__(self):
        self.IBIS_DIR.mkdir(parents=True, exist_ok=True)
```

**Acceptance:** Module compiles, IBIS directory created

---

#### Task 5.2: Implement serialization (2.5h)
```python
class IBISSerializer:
    def serialize_debate_to_ibis(
        self,
        prompt: str,
        debate_results: dict,
        decision_id: Optional[str] = None
    ) -> IBIS:
        """
        Convert debate results to IBIS structure.

        Args:
            prompt: Original question
            debate_results: Output from debate council
            decision_id: Optional ADR ID reference

        Returns:
            IBIS object with structured dialogue
        """
        ideas = []

        # Extract ideas from debate results
        for specialist, content in debate_results.get("specialists", {}).items():
            idea = self._extract_idea_from_specialist(specialist, content)
            if idea:
                ideas.append(idea)

        # Extract arguments
        for idea in ideas:
            idea.arguments = self._extract_arguments(
                debate_results, idea.proposal
            )

        return IBIS(
            issue=prompt,
            ideas=ideas,
            timestamp=datetime.utcnow().isoformat(),
            decision_id=decision_id,
            recommendation=debate_results.get("synthesis", {}).get("recommendation")
        )

    def _extract_idea_from_specialist(
        self,
        specialist: str,
        content: str
    ) -> Optional[IBISIdea]:
        """Extract proposal from specialist output."""
        # Look for recommendation/proposal in content
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith(("Recommendation:", "Proposal:", "Decision:")):
                proposal = line.split(":", 1)[1].strip()
                return IBISIdea(
                    id=f"idea_{specialist}_{hash(proposal) % 10000}",
                    proposal=proposal,
                    provider=specialist
                )
        return None

    def _extract_arguments(
        self,
        debate_results: dict,
        proposal: str
    ) -> List[IBISArgument]:
        """Extract pro/con arguments for a proposal."""
        arguments = []

        # Look for challenge results
        challenges = debate_results.get("challenges", {})
        for source, challenge_content in challenges.items():
            # Extract pros
            for line in challenge_content.split("\n"):
                if any(marker in line.lower() for marker in ["(+)", "pro:", "positive", "benefit"]):
                    arguments.append(IBISArgument(
                        type="pro",
                        text=line.split(":", 1)[1].strip() if ":" in line else line.strip(),
                        source=source
                    ))

            # Extract cons
            for line in challenge_content.split("\n"):
                if any(marker in line.lower() for marker in ["(-)", "con:", "negative", "risk", "concern"]):
                    arguments.append(IBISArgument(
                        type="con",
                        text=line.split(":", 1)[1].strip() if ":" in line else line.strip(),
                        source=source
                    ))

        return arguments
```

**Acceptance:** Correctly structures debate results

---

#### Task 5.3: Implement saving and retrieval (2h)
```python
class IBISSerializer:
    def save_ibis(self, ibis: IBIS, title_slug: str) -> str:
        """
        Save IBIS to JSON file.

        Args:
            ibis: IBIS object to save
            title_slug: URL-safe title for filename

        Returns:
            Path to saved file (forward slashes)
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        filename = f"ibis-{title_slug}-{timestamp}.json"
        filepath = self.IBIS_DIR / filename

        # Convert to dict and save
        data = self._ibis_to_dict(ibis)
        filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Update index
        self._update_index(ibis, str(filepath).replace("\\", "/"))

        return str(filepath).replace("\\", "/")

    def _ibis_to_dict(self, ibis: IBIS) -> dict:
        """Convert IBIS to JSON-serializable dict."""
        return {
            "issue": ibis.issue,
            "ideas": [
                {
                    "id": idea.id,
                    "proposal": idea.proposal,
                    "provider": idea.provider,
                    "arguments": [
                        {"type": arg.type, "text": arg.text, "source": arg.source}
                        for arg in idea.arguments
                    ]
                }
                for idea in ibis.ideas
            ],
            "timestamp": ibis.timestamp,
            "decision_id": ibis.decision_id,
            "recommendation": ibis.recommendation
        }

    def load_ibis(self, filepath: str) -> IBIS:
        """Load IBIS from JSON file."""
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
        return self._dict_to_ibis(data)

    def _update_index(self, ibis: IBIS, filepath: str):
        """Update IBIS index."""
        index_path = self.IBIS_DIR / "index.json"

        if index_path.exists():
            index = json.loads(index_path.read_text(encoding="utf-8"))
        else:
            index = {"decisions": []}

        index["decisions"].append({
            "issue": ibis.issue[:100],  # Truncate long issues
            "timestamp": ibis.timestamp,
            "decision_id": ibis.decision_id,
            "filepath": filepath
        })

        index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")
```

**Acceptance:** IBIS files saved and retrievable

---

### Day 2-3: Measurement Infrastructure (3-4 hours)

#### Task 6.1: Implement confidence measurement (2h)
```python
# File: P:/__csf.nip/src/lib/confidence_scorer.py

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ConfidenceScore:
    score: int  # 0-100
    breakdown: Dict[str, int]
    reasons: List[str]

class ConfidenceScorer:
    """
    Measures decision confidence based on objective criteria.

    Scoring Rubric:
    - Trade-offs documented: 20 points
    - Risks explicitly categorized: 15 points
    - ADR generated: 15 points
    - Multi-specialist agreement: 20 points
    - Quality attributes prioritized: 20 points
    - IBIS dialogue captured: 10 points
    """

    def measure(
        self,
        analysis_result: dict,
        has_adr: bool,
        has_ibis: bool,
        quality_attributes_count: int
    ) -> ConfidenceScore:
        """
        Calculate confidence score from decision artifacts.

        Returns:
            ConfidenceScore with total and breakdown
        """
        breakdown = {}
        reasons = []

        # 1. Trade-offs documented (20 points)
        tradeoff_score = self._score_tradeoffs(analysis_result)
        breakdown["tradeoffs"] = tradeoff_score
        if tradeoff_score < 20:
            reasons.append("Trade-offs not fully documented")

        # 2. Risks categorized (15 points)
        risk_score = self._score_risks(analysis_result)
        breakdown["risks"] = risk_score
        if risk_score < 15:
            reasons.append("Risks not explicitly categorized")

        # 3. ADR generated (15 points)
        adr_score = 15 if has_adr else 0
        breakdown["adr"] = adr_score
        if adr_score == 0:
            reasons.append("No ADR generated")

        # 4. Specialist agreement (20 points)
        agreement_score = self._score_agreement(analysis_result)
        breakdown["agreement"] = agreement_score
        if agreement_score < 20:
            reasons.append("Low specialist agreement")

        # 5. Quality attributes (20 points)
        qa_score = min(20, quality_attributes_count * 5)
        breakdown["quality_attributes"] = qa_score
        if qa_score < 20:
            reasons.append("Limited quality attribute analysis")

        # 6. IBIS captured (10 points)
        ibis_score = 10 if has_ibis else 0
        breakdown["ibis"] = ibis_score
        if ibis_score == 0:
            reasons.append("No IBIS dialogue captured")

        total = sum(breakdown.values())

        return ConfidenceScore(
            score=total,
            breakdown=breakdown,
            reasons=reasons if total < 100 else ["All criteria met"]
        )

    def _score_tradeoffs(self, result: dict) -> int:
        """Score trade-off documentation (0-20)."""
        tradeoffs = result.get("tradeoffs", [])
        if not tradeoffs:
            return 0

        # More detailed tradeoffs = higher score
        score = min(20, len(tradeoffs) * 5)
        return score

    def _score_risks(self, result: dict) -> int:
        """Score risk categorization (0-15)."""
        risks = result.get("risks", [])
        if not risks:
            return 0

        # Check for severity categorization
        has_severity = any("severity" in str(r).lower() for r in risks)
        base = min(10, len(risks) * 3)
        return base + (5 if has_severity else 0)

    def _score_agreement(self, result: dict) -> int:
        """Score specialist agreement (0-20)."""
        synthesis = result.get("synthesis", {})
        if not synthesis:
            return 0

        # Look for agreement indicators
        agreement = synthesis.get("agreement_score", 0)
        if isinstance(agreement, (int, float)):
            return int(agreement * 20)

        return 10  # Default if no explicit score
```

**Acceptance:** Scoring produces consistent 0-100 values

---

#### Task 6.2: Baseline measurement script (1.5h)
```python
# File: P:/__csf.nip/scripts/benchmark_confidence.py

"""
Baseline confidence measurement script.

Run this on existing decisions to establish baseline before Tier 1.
"""

import json
from pathlib import Path
from src.lib.confidence_scorer import ConfidenceScorer

def measure_baseline_decisions(decisions: List[dict]) -> dict:
    """
    Measure baseline confidence for existing decisions.

    Args:
        decisions: List of past decisions with analysis results

    Returns:
        Summary statistics
    """
    scorer = ConfidenceScorer()
    scores = []

    for decision in decisions:
        # Simulate baseline (no ADR, no IBIS, basic quality attrs)
        score = scorer.measure(
            analysis_result=decision.get("analysis", {}),
            has_adr=False,  # Baseline has no ADR
            has_ibis=False,  # Baseline has no IBIS
            quality_attributes_count=1  # Baseline has minimal QA
        )
        scores.append(score.score)

    return {
        "mean": sum(scores) / len(scores),
        "min": min(scores),
        "max": max(scores),
        "count": len(scores)
    }

def main():
    # Load sample past decisions
    decisions_path = Path("P:/__csf.nip/data/baseline_decisions.json")

    if decisions_path.exists():
        decisions = json.loads(decisions_path.read_text())
    else:
        # Create sample baseline
        decisions = create_sample_baseline()

    baseline = measure_baseline_decisions(decisions)

    print(f"Baseline Confidence: {baseline['mean']:.1f}%")
    print(f"Range: {baseline['min']:.0f}% - {baseline['max']:.0f}%")
    print(f"Decisions measured: {baseline['count']}")

    # Save for comparison
    output = Path("P:/__csf.nip/data/baseline_score.json")
    output.write_text(json.dumps(baseline, indent=2))

    return baseline

def create_sample_baseline() -> List[dict]:
    """Create sample baseline decisions for testing."""
    return [
        {
            "prompt": "Should we use REST or GraphQL?",
            "analysis": {
                "tradeoffs": ["REST simpler", "GraphQL more flexible"],
                "risks": ["GraphQL learning curve"]
            }
        },
        # ... more sample decisions
    ]
```

**Acceptance:** Produces comparable baseline scores

---

### Day 3-4: Final Testing & Decision Gate (4 hours)

#### Task 7.1: Integration with enhancement_router.py (2h)
```python
# File: P:/__csf.nip/src/lib/enhancement_router.py

# Add imports after line ~34
from src.lib.complexity_detector import ComplexityDetector
from src.lib.utility_tree_extractor import UtilityTreeBuilder
from src.lib.adr_formatter import ADRFormatter
from src.lib.ibis_serializer import IBISSerializer

# Add to SPECIALIST_ROLES after existing roles
SPECIALIST_ROLES = {
    # ... existing roles ...

    # Tier 1 Framework Specialists
    "adr_documentation": {
        "primary": "meta-llama/llama-3.3-70b@groq",
        "fallback": ["anthropic/claude-3.5-sonnet"],
        "framework": "Tyree-Akerman ADR Template",
        "role": "Generate standard decision records",
        "complexity_level": 1,  # All levels
    },
}

# Update route_enhanced method
async def route_enhanced(self, prompt: str, config: dict) -> dict:
    """
    Route enhancement request with Tier 1 framework integration.

    NEW: Complexity detection, quality attributes, ADR generation, IBIS capture.
    """
    # === NEW: Tier 1 Complexity Detection ===
    complexity_detector = ComplexityDetector()
    complexity = complexity_detector.detect_level(prompt)
    quality_tree = complexity_detector.extract_quality_attributes(prompt)

    # Format quality attributes for specialists
    qa_builder = UtilityTreeBuilder()
    quality_prompt = qa_builder.format_for_specialists(quality_tree)

    # === NEW: Get specialists for complexity level ===
    active_specialists = self._get_specialists_for_level(
        complexity.level, config
    )

    # === Inject quality attributes into specialist prompts ===
    enhanced_prompt = f"{prompt}\n\n{quality_prompt}"

    # Execute specialists in parallel
    results = await asyncio.gather(*[
        self._call_specialist(s, enhanced_prompt)
        for s in active_specialists
    ])

    # Aggregate results
    aggregated = self._aggregate_results(results)

    # === NEW: Generate ADR if configured ===
    adr_path = None
    if config.get("include_adr", True) and complexity.level.value >= 1:
        formatter = ADRFormatter()
        adr_content = formatter.generate_from_analysis(
            prompt=prompt,
            analysis_result=aggregated,
            quality_attributes=quality_tree,
            debate_results=aggregated.get("debate"),
            risk_analysis=aggregated.get("risk_analysis")
        )
        adr_path = formatter.save_adr(adr_content)

    # === NEW: Serialize IBIS dialogue ===
    ibis_path = None
    if config.get("include_ibis", True):
        serializer = IBISSerializer()
        ibis = serializer.serialize_debate_to_ibis(
            prompt=prompt,
            debate_results=aggregated.get("debate", {}),
            decision_id=adr_content.id if adr_path else None
        )
        title_slug = formatter._slugify_title(prompt)
        ibis_path = serializer.save_ibis(ibis, title_slug)

    # Add framework outputs to results
    aggregated["tier1_frameworks"] = {
        "complexity_level": complexity.level.value,
        "quality_attributes": [
            {"name": a.name, "weight": a.weight}
            for a in quality_tree.sorted_attributes()
        ],
        "adr_path": adr_path,
        "ibis_path": ibis_path
    }

    return aggregated

def _get_specialists_for_level(self, level: int, config: dict) -> List[str]:
    """Get active specialists based on complexity level."""
    # Tier 1 always includes basic specialists
    base_specialists = ["architecture", "performance"]

    if level >= 2:
        base_specialists.extend(["security", "scalability"])

    if level >= 3:
        base_specialists.extend(["risk_analysis", "cost_analysis"])

    if config.get("include_adr"):
        base_specialists.append("adr_documentation")

    return base_specialists
```

**Acceptance:** Enhancement router calls all Tier 1 components

---

#### Task 7.2: End-to-end test (1h)
```python
# File: P:/__csf.nip/tests/integration/test_tier1_e2e.py

import pytest
import asyncio
from src.lib.enhancement_router import EnhancementRouter

@pytest.mark.asyncio
async def test_tier1_e2e():
    """Test complete Tier 1 pipeline end-to-end."""
    router = EnhancementRouter()

    prompt = "Should we use REST or GraphQL for our API?"

    result = await router.route_enhanced(
        prompt=prompt,
        config={
            "include_adr": True,
            "include_ibis": True
        }
    )

    # Verify
    assert "tier1_frameworks" in result
    assert result["tier1_frameworks"]["complexity_level"] == 1
    assert len(result["tier1_frameworks"]["quality_attributes"]) > 0
    assert result["tier1_frameworks"]["adr_path"] is not None
    assert result["tier1_frameworks"]["ibis_path"] is not None

    # Verify files exist
    from pathlib import Path
    assert Path(result["tier1_frameworks"]["adr_path"]).exists()
    assert Path(result["tier1_frameworks"]["ibis_path"]).exists()

    print(f"ADR created: {result['tier1_frameworks']['adr_path']}")
    print(f"IBIS created: {result['tier1_frameworks']['ibis_path']}")
```

**Acceptance:** E2E test passes with all artifacts created

---

#### Task 7.3: Decision gate evaluation (1h)
```python
# File: P:/__csf.nip/scripts/evaluate_tier1_gate.py

"""
Decision Gate Evaluation Script

Run this at end of Week 2 to decide on Tier 2.
"""

from src.lib.confidence_scorer import ConfidenceScorer
from pathlib import Path
import json

def evaluate_decision_gate() -> dict:
    """
    Evaluate Tier 1 success criteria.

    Returns:
        GO/NO_GO decision with rationale
    """
    criteria = {
        "confidence_improvement": False,
        "provider_reliability": False,
        "complexity_accuracy": False,
        "adr_quality": False
    }

    reasons = []

    # 1. Check confidence improvement
    baseline = load_baseline()
    tier1_scores = load_tier1_scores()

    if tier1_scores:
        improvement = (tier1_scores["mean"] - baseline["mean"]) / baseline["mean"]
        if improvement >= 0.20:
            criteria["confidence_improvement"] = True
            reasons.append(f"Confidence improvement: {improvement*100:.1f}% (target: 20%)")
        else:
            reasons.append(f"Confidence improvement: {improvement*100:.1f}% (BELOW 20% threshold)")

    # 2. Check provider reliability
    provider_stats = load_provider_stats()
    if provider_stats["success_rate"] >= 0.99:
        criteria["provider_reliability"] = True
        reasons.append(f"Provider reliability: {provider_stats['success_rate']*100:.1f}%")
    else:
        reasons.append(f"Provider reliability: {provider_stats['success_rate']*100:.1f}% (BELOW 99%)")

    # 3. Check complexity detector
    detector_results = load_detector_results()
    if detector_results["accuracy"] >= 0.85:
        criteria["complexity_accuracy"] = True
        reasons.append(f"Complexity detector accuracy: {detector_results['accuracy']*100:.1f}%")
    else:
        reasons.append(f"Complexity detector accuracy: {detector_results['accuracy']*100:.1f}% (BELOW 85%)")

    # 4. Check ADR quality
    adr_review = load_adr_review()
    if adr_review["passes_standard"]:
        criteria["adr_quality"] = True
        reasons.append("ADR quality: Passes Tyree-Akerman standard")
    else:
        reasons.append("ADR quality: Does not pass standard")

    # Decision
    passed = sum(criteria.values())
    decision = "GO" if passed >= 3 else "NO_GO"

    return {
        "decision": decision,
        "criteria": criteria,
        "reasons": reasons,
        "passed_count": passed,
        "recommendation": get_recommendation(decided, passed)
    }

def get_recommendation(decision: str, passed: int) -> str:
    """Get recommendation based on gate results."""
    if decision == "GO":
        return "Proceed to Tier 2 implementation"
    elif passed == 2:
        return "Refine Tier 1 and re-measure (extend 1 week)"
    else:
        return "Pause development, reassess approach"

def main():
    result = evaluate_decision_gate()

    print("=" * 60)
    print(f"TIER 1 DECISION GATE: {result['decision']}")
    print("=" * 60)
    print("\nCriteria Results:")
    for criterion, passed in result['criteria'].items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {criterion}")

    print("\nRationale:")
    for reason in result['reasons']:
        print(f"  - {reason}")

    print(f"\nRecommendation: {result['recommendation']}")

    # Save results
    output = Path("P:/__csf.nip/.speckit/memory/tier1_gate_results.json")
    output.write_text(json.dumps(result, indent=2))

    return result

# Helper functions
def load_baseline() -> dict:
    path = Path("P:/__csf.nip/data/baseline_score.json")
    return json.loads(path.read_text()) if path.exists() else {"mean": 65}

def load_tier1_scores() -> dict:
    path = Path("P:/__csf.nip/data/tier1_scores.json")
    return json.loads(path.read_text()) if path.exists() else {}

def load_provider_stats() -> dict:
    path = Path("P:/__csf.nip/data/provider_stats.json")
    return json.loads(path.read_text()) if path.exists() else {"success_rate": 1.0}

def load_detector_results() -> dict:
    path = Path("P:/__csf.nip/data/detector_accuracy.json")
    return json.loads(path.read_text()) if path.exists() else {"accuracy": 0.90}

def load_adr_review() -> dict:
    path = Path("P:/__csf.nip/data/adr_quality_review.json")
    return json.loads(path.read_text()) if path.exists() else {"passes_standard": True}
```

**Acceptance:** Gate produces clear GO/NO_GO decision

---

## Configuration Files

### arch-defaults.yaml
```yaml
# File: P:/__csf.nip/src/config/arch-defaults.yaml

tier1:
  enabled: true
  complexity_detection:
    default_level: 1
    solo_dev_maintainability_boost: true
  adr:
    auto_generate: true
    directory: "P:/__csf.nip/adr"
    template: "tyree_akerman"
  ibis:
    auto_capture: true
    directory: "P:/__csf.nip/data/ibis"
  quality_attributes:
    default: "maintainability"
    solo_dev_weight: 1.0

complexity_levels:
  1:
    name: "Simple Decision"
    frameworks: ["adr", "ibis", "quality_tree"]
    estimated_duration: 30
    specialists: ["architecture"]
  2:
    name: "Architecture Design"
    frameworks: ["adr", "ibis", "quality_tree"]
    estimated_duration: 180
    specialists: ["architecture", "performance", "security"]
  3:
    name: "System-Wide Redesign"
    frameworks: ["adr", "ibis", "quality_tree", "risk_analysis"]
    estimated_duration: 300
    specialists: ["architecture", "performance", "security", "scalability", "risk_analysis"]
  4:
    name: "Compare Alternatives"
    frameworks: ["adr", "ibis", "quality_tree", "decision_matrix"]
    estimated_duration: 240
    specialists: ["architecture", "performance", "security", "cost_analysis"]

providers:
  adr_generation:
    primary: "meta-llama/llama-3.3-70b@groq"
    fallback: "anthropic/claude-3.5-sonnet"
  complexity_detection:
    primary: "anthropic/claude-3.5-sonnet"

measurement:
  baseline_score_path: "P:/__csf.nip/data/baseline_score.json"
  tier1_scores_path: "P:/__csf.nip/data/tier1_scores.json"
  target_improvement: 0.20  # 20%
```

---

## Summary Checklist

### Week 1 Deliverables
- [ ] ComplexityDetector module with >85% accuracy
- [ ] ADRFormatter generating Tyree-Akerman standard ADRs
- [ ] UtilityTreeBuilder extracting quality attributes
- [ ] Unit tests passing (100%)
- [ ] Integration tests passing

### Week 2 Deliverables
- [ ] IBISSerializer capturing debate dialogue
- [ ] ConfidenceScorer measuring decision quality
- [ ] Baseline measurement script
- [ ] enhancement_router.py integration complete
- [ ] End-to-end test passing

### Decision Gate (End of Week 2)
- [ ] Confidence improvement ≥ 20%?
- [ ] Provider reliability ≥ 99%?
- [ ] Complexity detector accuracy ≥ 85%?
- [ ] ADR quality passes standard?

**If 3+ YES → Proceed to Tier 2**
**If ≤2 YES → Refine Tier 1**

---

**Status:** Implementation plan complete, ready for execution

**Next Step:** Create tasks.json (Step 6: Task Decomposition)
