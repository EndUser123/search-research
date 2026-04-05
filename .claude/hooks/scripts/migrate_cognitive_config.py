#!/usr/bin/env python3
"""
Migration script for cognitive_reasoning_config.json

Migrates from legacy cognitive_enhancers_config.json to the unified
cognitive_reasoning_config.json format.

Usage:
    python P:/.claude/hooks/scripts/migrate_cognitive_config.py [--dry-run] [--backup]

Options:
    --dry-run    Show what would be migrated without making changes
    --backup     Create backup of existing config before migration
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path


def load_legacy_config(config_path: Path) -> dict:
    """Load legacy cognitive_enhancers_config.json."""
    if not config_path.exists():
        print(f"Warning: Legacy config not found at {config_path}")
        return {}

    with open(config_path, encoding='utf-8') as f:
        return json.load(f)


def create_unified_config(legacy: dict) -> dict:
    """Create unified config from legacy config."""
    unified = {
        "version": "1.0",
        "_COMMENT": "Unified configuration for Cognitive Reasoning Optimization system",
        "cognitive_frameworks": {
            "enabled": legacy.get("enabled", True),
            "frameworks": {
                "assumption_surfacing": legacy.get("assumption_surfacing", True),
                "outcome_anchoring": legacy.get("outcome_anchoring", True),
                "inversion_prompting": legacy.get("inversion_prompting", True),
                "chestertons_fence": legacy.get("chestertons_fence", True),
                "calibrated_confidence": legacy.get("calibrated_confidence", True),
                "socratic_decomposition": legacy.get("socratic_decomposition", True),
                "failure_analysis_soft": True
            },
            "max_enhancers_per_prompt": legacy.get("max_enhancers_per_prompt", 3),
            "socratic_min_length": legacy.get("socratic_min_length", 200),
            "min_prompt_length": legacy.get("min_prompt_length", 30),
            "topics": legacy.get("topics", {
                "implementation": True,
                "diagnostic": True,
                "meta_rca": True,
                "decomposition": True,
                "implementation_diagnostic": True
            }),
            "fap_semantic_enabled": legacy.get("fap_semantic_enabled", True),
            "fap_similarity_threshold": legacy.get("fap_similarity_threshold", 0.85)
        },
        "reasoning_modes": {
            "enabled": True,
            "confidence_min": 2,
            "confidence_high": 4,
            "modes": {
                "sequential": {
                    "enabled": True,
                    "description": "Step-by-step reasoning for low-confidence scenarios",
                    "confidence_threshold": 2
                },
                "multi_agent": {
                    "enabled": True,
                    "description": "Multi-agent deliberation for medium-confidence scenarios",
                    "confidence_threshold": 3
                },
                "reflective": {
                    "enabled": True,
                    "description": "Reflective reasoning with self-questioning for high-confidence scenarios",
                    "confidence_threshold": 4
                },
                "analytical": {
                    "enabled": True,
                    "description": "Deep analytical reasoning for complex problems",
                    "trigger_keywords": ["analyze", "investigate", "diagnose", "debug"]
                }
            },
            "default_mode": "sequential"
        },
        "think_profiles": {
            "enabled": True,
            "strong_count": 1,
            "weak_count": 2,
            "profiles": {
                "debug_rca": {
                    "enabled": True,
                    "strong_patterns": [
                        "debugging|debug|investigat",
                        "root cause|rca|diagnos",
                        "not working|broken|fail",
                        "error|exception|traceback"
                    ],
                    "weak_patterns": [
                        "fix|repair|resolve",
                        "issue|problem|bug",
                        "why|how come"
                    ]
                },
                "refactor_plan": {
                    "enabled": True,
                    "strong_patterns": [
                        "refactor|restructure|reorganize",
                        "plan|design|architecture",
                        "rethink|reconsider|revisit"
                    ],
                    "weak_patterns": [
                        "improve|optimize|enhance",
                        "reorganize|cleanup"
                    ]
                },
                "implementation": {
                    "enabled": True,
                    "strong_patterns": [
                        "implement|build|create",
                        "add feature|new functionality",
                        "write code|develop"
                    ],
                    "weak_patterns": [
                        "code|program|script",
                        "function|method|class"
                    ]
                },
                "architecture_review": {
                    "enabled": True,
                    "strong_patterns": [
                        "review architecture|design review",
                        "architectural decision|adr",
                        "system design|structure"
                    ],
                    "weak_patterns": [
                        "architecture|design pattern",
                        "structure|organization"
                    ]
                },
                "learning_synthesis": {
                    "enabled": True,
                    "strong_patterns": [
                        "what did you learn|lessons learned",
                        "summarize|synthesize|key takeaway",
                        "retrospective|post-mortem"
                    ],
                    "weak_patterns": [
                        "understand|explain|clarify",
                        "document|notes"
                    ]
                },
                "decision_analysis": {
                    "enabled": True,
                    "strong_patterns": [
                        "decide between|choice|option",
                        "tradeoff|trade-off|pros and cons",
                        "recommendation|suggest"
                    ],
                    "weak_patterns": [
                        "should i|what if|consider",
                        "alternatives|comparison"
                    ]
                },
                "verification": {
                    "enabled": True,
                    "strong_patterns": [
                        "verify|validate|confirm",
                        "test.*work|check.*correct",
                        "ensure|guarantee"
                    ],
                    "weak_patterns": [
                        "double-check|verify that",
                        "make sure|confirm"
                    ]
                }
            }
        },
        "questioning_patterns": {
            "enabled": True,
            "patterns_file": r"C:\Users\brsth\.claude\projects\P--\memory\questioning_patterns.md",
            "patterns": {
                "arbitrary_threshold": {
                    "enabled": True,
                    "trigger_question": "Why this specific value?",
                    "detection_trigger": "Any time I catch myself thinking 'that seems reasonable' without data"
                },
                "concurrency_safety": {
                    "enabled": True,
                    "trigger_question": "Are you sure about concurrency?",
                    "detection_trigger": "Any proposal that uses centralized/shared state in a multi-terminal environment"
                },
                "over_engineering": {
                    "enabled": True,
                    "trigger_question": "Is this optimal or over-engineering?",
                    "detection_trigger": "Pre-mortem analysis with more than 3 priority items"
                },
                "scale_analysis": {
                    "enabled": True,
                    "trigger_question": "What happens at scale?",
                    "detection_trigger": "Proposals that involve updating more than 3-5 files"
                },
                "debugging_cognition": {
                    "enabled": True,
                    "trigger_questions": [
                        "What does the error actually say?",
                        "What hypotheses can we test simultaneously?",
                        "What's on the error stack vs. what's in my head?"
                    ],
                    "heuristics": {
                        "entry_point_first": "Run failing code directly before hypothesis generation",
                        "parallel_diagnostics": "Test multiple hypotheses simultaneously instead of sequentially",
                        "meta_cognitive_preflight": "Ask 'What does the error actually say?' before proposing solutions"
                    },
                    "detection_trigger": "Any debugging investigation or error diagnosis"
                }
            }
        },
        "performance": {
            "max_detection_ms": 60.0,
            "enable_monitoring": True,
            "monitoring": {
                "log_slow_detections": True,
                "slow_detection_threshold_ms": 30.0,
                "log_interval_seconds": 300
            }
        },
        "modes": legacy.get("modes", {
            "rca": {
                "topic": "meta_rca",
                "description": "Force meta_rca topic for root cause analysis"
            },
            "deep": {
                "topic": "implementation",
                "description": "Force implementation topic for deep work"
            },
            "fast": {
                "max_enhancers": 2,
                "lightweight_only": True,
                "description": "Fast mode: cap to 2 lightweight cognitive enhancers"
            }
        }),
        "skills": {
            "enhance_skills": legacy.get("enhance_skills", True),
            "skip_skills": legacy.get("skip_skills", [])
        }
    }

    return unified


def backup_config(config_path: Path) -> Path:
    """Create backup of existing config."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = config_path.parent / f"{config_path.stem}.backup.{timestamp}{config_path.suffix}"
    shutil.copy2(config_path, backup_path)
    print(f"Backup created: {backup_path}")
    return backup_path


def write_unified_config(config: dict, output_path: Path) -> None:
    """Write unified config to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"Unified config written: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Migrate cognitive configuration")
    parser.add_argument("--dry-run", action="store_true", help="Show migration without making changes")
    parser.add_argument("--backup", action="store_true", help="Create backup before migration")
    args = parser.parse_args()

    # Determine paths
    hooks_dir = Path("P:/.claude/hooks")
    legacy_path = hooks_dir / "cognitive_enhancers_config.json"
    unified_path = hooks_dir / "cognitive_reasoning_config.json"

    # Load legacy config
    print(f"Loading legacy config from: {legacy_path}")
    legacy = load_legacy_config(legacy_path)

    if not legacy:
        print("No legacy config found. Using defaults.")

    # Create unified config
    print("Creating unified configuration...")
    unified = create_unified_config(legacy)

    # Dry run - just show what would be done
    if args.dry_run:
        print("\n=== DRY RUN ===")
        print(json.dumps(unified, indent=2))
        print(f"\nWould write to: {unified_path}")
        return

    # Backup existing unified config if it exists
    if unified_path.exists() and args.backup:
        backup_config(unified_path)

    # Write unified config
    write_unified_config(unified, unified_path)

    # Summary
    print("\n=== Migration Summary ===")
    print(f"Migrated settings from: {legacy_path}")
    print(f"Unified config written: {unified_path}")
    print("\nConsolidated settings:")
    print(f"  • Cognitive frameworks: {len(unified['cognitive_frameworks']['frameworks'])} enhancers")
    print(f"  • Reasoning modes: {len(unified['reasoning_modes']['modes'])} modes")
    print(f"  • Think profiles: {len(unified['think_profiles']['profiles'])} profiles")
    print(f"  • Questioning patterns: {len(unified['questioning_patterns']['patterns'])} patterns")
    print(f"  • Performance thresholds: max {unified['performance']['max_detection_ms']}ms")


if __name__ == "__main__":
    main()
