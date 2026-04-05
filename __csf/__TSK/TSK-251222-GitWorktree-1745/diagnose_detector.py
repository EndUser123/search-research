#!/usr/bin/env python3
"""Diagnostic script for explore opportunity detector."""
from __future__ import annotations

import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path("P:/").resolve() / ".claude" / "hooks"
sys.path.insert(0, str(hooks_dir))

from explore_opportunity_detector import ExploreOpportunityDetector

# Create detector
detector = ExploreOpportunityDetector()

# Test prompts
prompts = [
    "I want to understand the codebase architecture",
    "Explore the authentication system components",
    "What design patterns are used in this project?",
    "How does this work?",
]

for prompt in prompts:
    print(f"\nPrompt: {prompt}")
    print("-" * 60)

    # Test each component
    exploration = detector._analyze_exploration_intent(prompt)
    question = detector._analyze_question_patterns(prompt)
    vagueness = detector._analyze_vagueness(prompt)
    context = detector._analyze_context_awareness(prompt, {"cwd": "P:/__csf"})
    file_refs = detector._count_file_references(prompt)

    # Calculate probability
    prob = exploration * 0.45 + question * 0.40 + vagueness * 0.10
    if file_refs == 0:
        prob += 0.05
    prob += context * 0.05

    print(f"  Exploration intent: {exploration:.3f} * 0.45 = {exploration * 0.45:.3f}")
    print(f"  Question patterns: {question:.3f} * 0.40 = {question * 0.40:.3f}")
    print(f"  Vagueness: {vagueness:.3f} * 0.10 = {vagueness * 0.10:.3f}")
    print(f"  File refs: {file_refs} -> +{0.05 if file_refs == 0 else 0:.3f}")
    print(f"  Context: {context:.3f} * 0.05 = {context * 0.05:.3f}")
    print(f"  -> TOTAL: {prob:.3f} ({prob*100:.1f}%)")
    print(f"  -> PASS: {prob >= 0.60}")

    # Check keywords
    print("\n  Keyword matches:")
    prompt_lower = prompt.lower()
    for category, config in detector.exploration_patterns.items():
        keywords = config["keywords"]
        matches = [kw for kw in keywords if kw in prompt_lower]
        if matches:
            print(f"    {category}: {', '.join(matches)}")
