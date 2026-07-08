"""
Tests for abstraction_audit_manifest.py — evidence harness for /ask audits.

Strategy:
- Layer: unit (deterministic file I/O + text scan; no network, no process boundary)
- What each test proves: file inventory correctness, search-term enumeration,
  risk-flag heuristics, output file generation, coverage_authority invariants
- What unit tests miss: real-repo performance (large tree), live dispatch behavior
  (irrelevant — this is whole-repo static evidence by design)

Fixture: a small temporary directory tree with known files and known content.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# ─── Path to the module under test ────────────────────────────────────────────

ASK_DIR = Path(__file__).resolve().parent.parent
ASK_SKILL = ASK_DIR / "SKILL.md"
MODULE_PATH = ASK_DIR / "lib" / "abstraction_audit_manifest.py"
TESTS_DIR = ASK_DIR / "tests"
PLUGIN_ROOT = ASK_DIR.parent.parent  # cc-skills-architect


# ─── Fixture: small synthetic repo ────────────────────────────────────────────

@pytest.fixture()
def fixture_repo(tmp_path: Path) -> Path:
    """
    Build a minimal repo tree with known files, content, and structure.
    Every file name and content line is chosen so the manifest hits are predictable.
    """
    root = tmp_path / "repo"
    root.mkdir()

    # skills/
    (root / "skills").mkdir()
    (root / "skills" / "SKILL.md").write_text(
        "# Skill\n\nUse Completion Evidence Contract before claiming done.\n"
        "Coverage_authority must be named.\n",
        encoding="utf-8",
    )

    # commands/
    (root / "commands").mkdir()
    (root / "commands" / "deploy.md").write_text(
        "# Deploy\n\nRuntime enforced when hook fires.\n"
        "Prompt advisory only if no hook.\n",
        encoding="utf-8",
    )

    # references/
    (root / "references").mkdir()
    (root / "references" / "evidence-tiers.md").write_text(
        "# Evidence\n\nObserved > Inferred > Unverified.\n"
        "Activation Truth: source_changed → behavior_observed.\n",
        encoding="utf-8",
    )

    # hooks/
    (root / "hooks").mkdir()
    (root / "hooks" / "my_hook.py").write_text(
        '# hook\nimport json\ndef run():\n    pass  # except: pass near telemetry jsonl\n'
        '    try:\n        telemetry_log()\n    except: pass\n',
        encoding="utf-8",
    )

    # tests/
    (root / "tests").mkdir()
    (root / "tests" / "test_smoke.py").write_text(
        "def test_pass():\n    assert True\n",
        encoding="utf-8",
    )

    # evals/
    (root / "evals").mkdir()
    (root / "evals" / "gold_v1.jsonl").write_text(
        '{"prompt": "test"}\n',
        encoding="utf-8",
    )

    # registries
    (root / "plugin.json").write_text(
        '{"name": "test-plugin"}\n',
        encoding="utf-8",
    )

    # file with risk flags
    (root / "risky.md").write_text(
        "# Report\n\nFull coverage achieved.\n"
        "Say the word and I will run it.\n"
        "/wiki-ingest this transcript.\n",
        encoding="utf-8",
    )

    # file with missing-term-sensitive content
    (root / "no-evals.md").write_text(
        "# Eval gap\n\nNo detection eval or prevention eval found.\n"
        "No runtime-ground-truth freshness field present.\n",
        encoding="utf-8",
    )

    # empty / non-text file (should be skipped)
    (root / "image.png").write_bytes(b"\x89PNG")
    (root / "empty").write_text("")

    return root


# ─── Test: script runs on a small fixture repo ───────────────────────────────

def test_script_runs_on_fixture(fixture_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "manifest_out"
    result = subprocess.run(
        [sys.executable, str(MODULE_PATH), "--repo-root", str(fixture_repo),
         "--out-dir", str(out_dir)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert out_dir.is_dir()
    # stdout prints the output dir path
    assert str(out_dir) in result.stdout.strip()


# ─── Test: manifest.json and manifest.md are written ──────────────────────────

def test_output_files_written(fixture_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(MODULE_PATH), "--repo-root", str(fixture_repo),
         "--out-dir", str(out_dir)],
        capture_output=True, text=True, timeout=30,
    )
    assert (out_dir / "manifest.json").exists()
    assert (out_dir / "manifest.md").exists()
    assert (out_dir / "search_hits.jsonl").exists()
    assert (out_dir / "file_inventory.json").exists()


# ─── Test: inventory counts are correct ───────────────────────────────────────

def test_inventory_counts(fixture_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(MODULE_PATH), "--repo-root", str(fixture_repo),
         "--out-dir", str(out_dir)],
        capture_output=True, text=True, timeout=30,
    )
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    counts = manifest["counts"]

    assert counts["skills"] == 1      # skills/SKILL.md
    assert counts["commands"] == 1    # commands/deploy.md
    assert counts["references"] == 1  # references/evidence-tiers.md
    assert counts["hooks"] == 1       # hooks/my_hook.py
    assert counts["tests"] == 1       # tests/test_smoke.py
    assert counts["evals"] == 1       # evals/gold_v1.jsonl
    assert counts["registries"] == 1  # plugin.json
    # risky.md, no-evals.md, empty → "other" (3 total)


# ─── Test: required search terms are all in the vocabulary ────────────────────

def test_all_search_terms_present_in_vocabulary() -> None:
    """Every term the user specified is in the SEARCH_TERMS list."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("mod", str(MODULE_PATH))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    required = [
        "Deeper Abstraction", "abstraction-opportunity", "Completion Evidence",
        "CEC", "Thought Partner", "Partner Posture", "Cross-Skill Transfer",
        "XSTC", "discoverability", "coverage_authority", "Activation Truth",
        "runtime enforced", "prompt advisory", "behavior eval", "gold corpus",
        "telemetry", "verification packet", "bounded action", "say the word",
        "wiki ingest", "report-contracts", "routing-by-affordances", "handoff",
        "no new command", "claim ledger", "disallowed conclusions",
        "prevention eval", "detection eval", "runtime-ground-truth",
        "stale ground truth",
    ]
    vocab = set(mod.SEARCH_TERMS)
    missing = [t for t in required if t not in vocab]
    assert not missing, f"Missing from SEARCH_TERMS: {missing}"


# ─── Test: hits_by_term for fixture content ──────────────────────────────────

def test_hits_found_for_fixture_content(fixture_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(MODULE_PATH), "--repo-root", str(fixture_repo),
         "--out-dir", str(out_dir)],
        capture_output=True, text=True, timeout=30,
    )
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    hits = manifest["hits_by_term"]

    # skills/SKILL.md mentions "Completion Evidence" and "coverage_authority"
    assert "skills/SKILL.md" in hits.get("Completion Evidence", [])
    assert "skills/SKILL.md" in hits.get("coverage_authority", [])

    # references/evidence-tiers.md mentions "Activation Truth"
    assert "references/evidence-tiers.md" in hits.get("Activation Truth", [])

    # commands/deploy.md mentions "runtime enforced" and "prompt advisory"
    assert "commands/deploy.md" in hits.get("runtime enforced", [])
    assert "commands/deploy.md" in hits.get("prompt advisory", [])

    # risky.md mentions "say the word" (space) and "wiki-ingest" (hyphen + slash)
    assert "risky.md" in hits.get("say the word", [])
    # /wiki-ingest matches the "wiki-ingest" search term (not "wiki ingest")
    assert "risky.md" in hits.get("wiki-ingest", [])


# ─── Test: missing terms reported ─────────────────────────────────────────────

def test_missing_terms_reported(fixture_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(MODULE_PATH), "--repo-root", str(fixture_repo),
         "--out-dir", str(out_dir)],
        capture_output=True, text=True, timeout=30,
    )
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    # Fixture has no content for many terms — missing_terms should be non-empty
    assert len(manifest["missing_terms"]) > 0
    # Specific term that fixture definitely lacks
    assert "disallowed conclusions" in manifest["missing_terms"]


# ─── Test: except:pass near telemetry is flagged ──────────────────────────────

def test_telemetry_swallowing_flagged(fixture_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(MODULE_PATH), "--repo-root", str(fixture_repo),
         "--out-dir", str(out_dir)],
        capture_output=True, text=True, timeout=30,
    )
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    flagged = manifest["risk_flags"]["telemetry_swallowing"]
    assert any("my_hook.py" in f for f in flagged), (
        f"hooks/my_hook.py should be flagged for except:pass near telemetry; "
        f"got: {flagged}"
    )


# ─── Test: "say the word" is flagged ──────────────────────────────────────────

def test_permission_deferral_flagged(fixture_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(MODULE_PATH), "--repo-root", str(fixture_repo),
         "--out-dir", str(out_dir)],
        capture_output=True, text=True, timeout=30,
    )
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    flagged = manifest["risk_flags"]["permission_deferral_language"]
    assert any("risky.md" in f for f in flagged)


# ─── Test: /wiki-ingest is flagged ───────────────────────────────────────────

def test_wiki_ingest_flagged(fixture_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(MODULE_PATH), "--repo-root", str(fixture_repo),
         "--out-dir", str(out_dir)],
        capture_output=True, text=True, timeout=30,
    )
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    flagged = manifest["risk_flags"]["wiki_ingest_or_auto_write"]
    assert any("risky.md" in f for f in flagged)


# ─── Test: runtime/advisory confusion is flagged ──────────────────────────────

def test_runtime_advisory_confusion_flagged(fixture_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(MODULE_PATH), "--repo-root", str(fixture_repo),
         "--out-dir", str(out_dir)],
        capture_output=True, text=True, timeout=30,
    )
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    flagged = manifest["risk_flags"]["runtime_advisory_confusion"]
    assert any("commands/deploy.md" in f for f in flagged), (
        "commands/deploy.md has 'runtime enforced' + 'prompt advisory' → should flag"
    )


# ─── Test: missing feedback-loop terms flagged ────────────────────────────────

def test_missing_feedback_loop_terms_flagged(fixture_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(MODULE_PATH), "--repo-root", str(fixture_repo),
         "--out-dir", str(out_dir)],
        capture_output=True, text=True, timeout=30,
    )
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    missing_fl = manifest["risk_flags"]["missing_feedback_loop_terms"]
    # no-evals.md DOES contain "detection eval", "prevention eval", "runtime-ground-truth"
    # (substrings inside "No detection eval or prevention eval found."), so they are
    # NOT missing — the fixture is constructed to have them present. Verify the
    # risk flag distinguishes present from absent.
    assert "detection eval" not in missing_fl
    assert "prevention eval" not in missing_fl
    # These terms genuinely have no fixture content
    assert "disallowed conclusions" in missing_fl
    assert "stale ground truth" in missing_fl


# ─── Test: coverage_authority is whole_repo_static ────────────────────────────

def test_coverage_authority_whole_repo_static(fixture_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(MODULE_PATH), "--repo-root", str(fixture_repo),
         "--out-dir", str(out_dir)],
        capture_output=True, text=True, timeout=30,
    )
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["coverage_authority"] == "whole_repo_static"
    # Markdown must also state it
    md = (out_dir / "manifest.md").read_text(encoding="utf-8")
    assert "whole_repo_static" in md


# ─── Test: manifest.md contains required sections ─────────────────────────────

def test_manifest_md_has_required_sections(fixture_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(MODULE_PATH), "--repo-root", str(fixture_repo),
         "--out-dir", str(out_dir)],
        capture_output=True, text=True, timeout=30,
    )
    md = (out_dir / "manifest.md").read_text(encoding="utf-8")
    for heading in ("Counts", "Missing Terms", "Risk Flags", "Recommended Read Set", "Proof Limits"):
        assert f"## {heading}" in md, f"manifest.md missing section: {heading}"


# ─── Test: search_hits.jsonl has correct structure ────────────────────────────

def test_search_hits_jsonl_structure(fixture_repo: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(MODULE_PATH), "--repo-root", str(fixture_repo),
         "--out-dir", str(out_dir)],
        capture_output=True, text=True, timeout=30,
    )
    lines = (out_dir / "search_hits.jsonl").read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) > 0
    first = json.loads(lines[0])
    assert "term" in first
    assert "path" in first


# ─── Test: no new top-level command created ───────────────────────────────────

def test_no_new_command_in_skill() -> None:
    """The script must not register any new slash command in any SKILL.md.

    A slash command is `/<name>` at the start of a line (frontmatter trigger) or
    after a space/bullet in the body. The artifact directory
    `.artifacts/abstraction-audit/` is a filesystem path, NOT a command — and
    the test must not flag it.
    """
    import re
    skill_text = ASK_SKILL.read_text(encoding="utf-8")

    # Frontmatter triggers: lines like `  - /foo`
    frontmatter_triggers = re.findall(r"^\s*-\s*(/[a-z][\w-]*)", skill_text, flags=re.M)
    # Body commands: `/name` after whitespace (not preceded by `.`)
    body_commands = re.findall(r"(?:^|[\s,(\[])(/[a-z][\w-]*)", skill_text, flags=re.M)

    all_commands = set(frontmatter_triggers) | set(body_commands)
    for forbidden in ("/abstraction-audit", "/audit-manifest", "/abstraction-audit-manifest"):
        assert forbidden not in all_commands, (
            f"{forbidden} introduced as a slash command — script must not add new commands"
        )


# ─── Test: module selfcheck (if present) ──────────────────────────────────────

def test_module_has_main() -> None:
    """Script must be runnable as __main__."""
    text = MODULE_PATH.read_text(encoding="utf-8")
    assert '__name__ == "__main__"' in text or "__name__ == '__main__'" in text
