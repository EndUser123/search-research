import json
import sys


sys.path.insert(0, "P:/.agents/skills/wiki-yt/scripts")
import write_pages


def _concept(slug: str) -> dict:
    return {
        "slug": slug,
        "title": slug.replace("-", " ").title(),
        "definition": "A validated definition.",
        "notebook_id": "nb-1",
        "notebook_title": "Notebook",
        "source_ids": ["source-1"],
        "claims": [],
        "disposition": "new",
        "synthesis_quality": "llm_validated",
    }


def test_validation_failure_does_not_promote_any_candidate(monkeypatch, tmp_path):
    input_path = tmp_path / "reconciled.json"
    input_path.write_text(json.dumps([_concept("good"), _concept("bad")]), encoding="utf-8")
    vault = tmp_path / "vault"
    staging = tmp_path / "staging"

    monkeypatch.setattr(
        write_pages,
        "validate",
        lambda path, _validator: (path.name != "bad.md", "invalid" if path.name == "bad.md" else ""),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "write_pages.py",
            "--input", str(input_path),
            "--vault", str(vault),
            "--validator", str(tmp_path / "validator.py"),
            "--staging", str(staging),
        ],
    )

    assert write_pages.main() == 5
    assert not (vault / "concepts" / "good.md").exists()
    assert not (vault / "concepts" / "bad.md").exists()
    assert (staging / "candidates" / "good.md").exists()
    assert (staging / "candidates" / "bad.md").exists()


def test_all_valid_candidates_promote_atomically(monkeypatch, tmp_path):
    input_path = tmp_path / "reconciled.json"
    input_path.write_text(json.dumps([_concept("good")]), encoding="utf-8")
    vault = tmp_path / "vault"
    staging = tmp_path / "staging"

    monkeypatch.setattr(write_pages, "validate", lambda _path, _validator: (True, ""))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "write_pages.py",
            "--input", str(input_path),
            "--vault", str(vault),
            "--validator", str(tmp_path / "validator.py"),
            "--staging", str(staging),
        ],
    )

    assert write_pages.main() == 0
    assert (vault / "concepts" / "good.md").exists()
    assert not staging.exists()
