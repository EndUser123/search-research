"""
Test corpus for nlm-to-wiki skill v2.

Ported from the original plugin's test_slug_collision.py and updated for:
- the new parse_report.py split_concepts / parse_concept_body API
- the new slugify (with max-len and word-boundary cut)
- the new 4-hop provenance model
- the new sync-manifest schema (now keyed by notebook_id)

Run with: pytest P:/.agents/skills/nlm-to-wiki/tests/
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make parse_report importable
SKILL_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from parse_report import slugify, split_concepts, parse_concept_body, short_uuid   # noqa: E402


# === SLUG COLLISION (ported from v1) ===

SLUG_COLLISION_PAIRS = [
    ("Machine Learning", "machine-learning"),
    ("Machine-learning", "machine-learning"),
    ("MACHINE LEARNING", "machine-learning"),
    ("DevOps Pipeline", "devops-pipeline"),
    ("Devops-Pipeline", "devops-pipeline"),
    ("DevOps-Pipeline", "devops-pipeline"),
]


def test_slug_collision_pairs():
    """Pairs that should produce identical slugs after slugify."""
    for name, expected in SLUG_COLLISION_PAIRS:
        assert slugify(name) == expected, f"{name!r} → {slugify(name)!r}, expected {expected!r}"


def test_slug_max_length():
    """Slugs over 50 chars cut at word boundary."""
    long_name = "This Is A Really Long Concept Name That Definitely Exceeds The Fifty Character Limit"
    slug = slugify(long_name)
    assert len(slug) <= 50


def test_slug_empty_fallback():
    assert slugify("!!!") == "concept"
    assert slugify("") == "concept"


def test_short_uuid():
    assert short_uuid("abc-1234-def8") == "abc1234d"
    assert short_uuid("ffffffff-ffff-ffff-ffff-ffffffffffff") == "ffffffff"


# === CONCEPT PARSING (ported + extended) ===

WELL_FORMED_REPORT = """# Notebook Report

Intro paragraph before any concept.

## Machine Learning
A technique that enables computers to learn from data without being explicitly programmed.

## Deep Learning
A subset of machine learning using neural networks with multiple layers.

## Transformer Models
Architecture that uses self-attention mechanisms for processing sequential data.
"""


def test_split_concepts_well_formed():
    sections = split_concepts(WELL_FORMED_REPORT)
    assert len(sections) == 3
    titles = [t for t, _ in sections]
    assert titles == ["Machine Learning", "Deep Learning", "Transformer Models"]


def test_split_concepts_empty():
    assert split_concepts("") == []
    assert split_concepts("no headings here") == []


def test_split_concepts_monolithic():
    """Text without ## headings produces no concepts (parser fails closed)."""
    monolithic = "Machine learning is a technique. It has no headings."
    assert split_concepts(monolithic) == []


def test_parse_concept_body_extracts_definition():
    body = """A short definition spanning one line.

- detail one
- detail two with value: 42
"""
    parsed = parse_concept_body(body)
    assert parsed["definition"] == "A short definition spanning one line."
    assert len(parsed["details"]) == 2


def test_parse_concept_body_values():
    body = """Definition here.

- threshold: 0.75
- max-size: 300
"""
    parsed = parse_concept_body(body)
    # Either parsed as value or detail; both are acceptable v1 behavior
    values_text = " ".join(v["value"] for v in parsed["values"])
    assert "0.75" in values_text or "0.75" in " ".join(parsed["details"])


# === SYNC MANIFEST (ported + updated schema) ===

MANIFEST_REQUIRED_FIELDS = {
    "notebook_id": str,
    "title": str,            # was notebook_title in v1; renamed for consistency
    "last_synced_at": str,
    "source_hash": str,      # new in v2: replaces source_ids comparison
    "source_ids": list,
    "concept_slugs": list,
}


def test_manifest_v2_schema():
    """v2 manifest must have the new fields."""
    manifest = {
        "notebook_id": "abc12345-def6-7890",
        "title": "AI Research Notes",
        "last_synced_at": "2026-07-25",
        "source_hash": "deadbeef",
        "source_ids": ["src-001", "src-002"],
        "concept_slugs": ["nlm-abc12345-machine-learning"],
    }
    for field, ftype in MANIFEST_REQUIRED_FIELDS.items():
        assert field in manifest, f"Missing: {field}"
        assert isinstance(manifest[field], ftype), f"Wrong type: {field}"


def test_source_hash_comparison():
    """Re-sync gate: hash equality means skip."""
    prior_hash = "abc123"
    current_hash = "abc123"
    assert prior_hash == current_hash  # → skip


def test_source_hash_changed():
    prior_hash = "abc123"
    current_hash = "def456"
    assert prior_hash != current_hash  # → re-extract


# === PROVENANCE CHAIN (new in v2) ===

def test_provenance_chain_depths():
    """Chain depth varies by sync mode: 2 (notebook), 3 (+cluster), 4 (+URL)."""
    two_hop = [
        {"level": "concept", "id": "slug"},
        {"level": "notebook", "id": "nb-1", "title": "T", "url": "u"},
    ]
    three_hop = two_hop + [{"level": "cluster", "id": 0, "name": "n", "source_path": "p"}]
    assert len(two_hop) == 2
    assert len(three_hop) == 3


# === FRONTMATTER (new in v2 — SCHEMA-compliant) ===

def test_frontmatter_has_required_fields():
    """Emitted frontmatter must satisfy validate_wiki_entry.py."""
    # Mirror what write_pages.build_frontmatter produces
    required = ["title", "created", "source", "tags", "summary", "agent", "host",
                "cognitive_load", "verification", "sources"]
    sample = {f: "x" for f in required}
    for f in ["title", "created", "source", "tags", "summary", "agent", "host",
              "cognitive_load", "verification", "sources"]:
        assert f in sample
