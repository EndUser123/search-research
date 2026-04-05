# Architecture Decision: Optimal Long-Term Solutions for media-pipeline

**Date:** 2026-02-28
**Template:** fast
**Query:** what do you think are optimal long term solutions?

## Decision Statement

Three targeted improvements: (1) enhanced verification feedback for recruiter-facing quality, (2) README pre-check to improve verification scores, (3) git-based asset versioning. Goal: make verification output compelling and actionable while keeping implementation minimal.

## Options

### For Enhanced Verification Feedback

**Option A:** Structured regeneration suggestions
- Pro: Tells users exactly what to regenerate with what prompt
- Con: Requires careful prompt engineering to avoid hallucination
- **Differs on:** Actionability vs. raw scores

**Option B:** Pass/fail only
- Pro: Simple
- Con: Not compelling for recruiters, doesn't guide improvement
- **Differs on:** Feedback depth

### For README Pre-Check

**Option A:** `gen-media analyze-readme` subcommand
- Pro: Separate step, doesn't interfere with generation workflow
- Con: Extra command users might skip
- **Differs on:** Workflow integration

**Option B:** Auto-check before verification
- Pro: Can't miss it
- Con: Annoying if user knows their README is good
- **Differs on:** Automatic vs. explicit

### For Asset Versioning

**Option A:** Git-based (commit assets with metadata in commit message)
- Pro: Native to Git, diff-able, rollback with standard tools
- Con: Requires committing generated assets (might not be desired)
- **Differs on:** Storage location

**Option B:** JSON tracking file (`media/.history.json`)
- Pro: Lightweight, no repo pollution
- Con: Can get out of sync with actual files
- **Differs on:** Data structure

## Recommendation

**Enhanced feedback:** Option A - structured regeneration suggestions. Recruiter care about "what did you measure and what did you do about it?" A score without action plan is noise.

**README pre-check:** Option A - separate subcommand. Let users opt-in to analysis. Auto-checking creates friction for experienced users who know their README is solid.

**Versioning:** Option A - git-based. User's repo is already the source of truth for everything else. Adding JSON tracking is duplicate state. Commit generated assets with structured commit messages:
```
gen-media: banner.png for debugRCA

Provider: openrouter (flux/pro)
Prompt hash: abc123
Quality score: 72/100
Generated: 2026-02-28T10:00:00Z
```

## Implementation

### 1. Enhanced Verification Feedback

**File:** `src/media_pipeline/verification/reporter.py` (new)

```python
@dataclass
class RegenerationSuggestion:
    """Actionable recommendation for improving media quality."""

    missing_features: list[str]
    suggested_focus: str
    example_prompt: str

    @classmethod
    def from_validation_report(cls, report: ValidationReport) -> "RegenerationSuggestion":
        """Extract actionable suggestions from validation report."""
        missing = [f.name for f in report.package_features if not f.covered]

        if not missing:
            return None

        focus = ", ".join(missing[:3])  # Top 3 missing
        return cls(
            missing_features=missing,
            suggested_focus=focus,
            example_prompt=f"Include visual representation of: {focus}"
        )
```

**Integration:** Modify `executor.py` to append suggestions to verification output:

```python
# In Executor._execute_verification()
suggestion = RegenerationSuggestion.from_validation_report(report)
if suggestion and report.quality_score < 70:
    console.print("\n[bold yellow]💡 Regeneration Recommendations:[/bold yellow]")
    console.print(f"  Missing: {', '.join(suggestion.missing_features)}")
    console.print(f"  Focus: {suggestion.suggested_focus}")
    console.print(f"  Prompt: gen-media video --focus \"{suggestion.suggested_focus}\"")
```

### 2. README Pre-Check

**File:** `src/media_pipeline/cli.py` (add new command)

```python
@cli.command()
@click.argument("repo_path", type=click.Path(exists=True))
def analyze_readme(repo_path: str) -> None:
    """Analyze README for feature extraction quality.

    Shows what features would be extracted before verification,
    allowing users to improve README before generating media.
    """
    from media_pipeline.classifier import analyze_repo
    from media_pipeline.verification import FeatureExtractor

    repo_info = analyze_repo(Path(repo_path))
    extractor = FeatureExtractor()
    features = extractor.extract_features(repo_info.concept_text)

    console.print(f"[bold]Analyzed:[/bold] {repo_info.readme_path}")
    console.print(f"[bold]Features found:[/bold] {len(features)}")

    for feature in features:
        console.print(f"  ✅ {feature.name}")

    if len(features) < 3:
        console.print("\n[yellow]⚠️  Low feature count may affect verification scores.")
        console.print("Consider adding a 'Features' section to README with:")
        console.print("  - Feature name (bold)")
        console.print("  - One-line description")
        console.print("  - Usage example")
```

### 3. Git-Based Versioning

**File:** `src/media_pipeline/executor.py` (modify execution result handling)

```python
import subprocess
from datetime import datetime UTC

def _commit_generated_asset(asset_path: Path, metadata: dict) -> None:
    """Commit generated asset with structured metadata."""

    # Commit message format
    features = metadata.get("features", [])
    provider = metadata.get("provider", "unknown")
    quality = metadata.get("quality_score", "N/A")

    message = f"""gen-media: {asset_path.name}

Provider: {provider}
Quality: {quality}/100
Generated: {datetime.now(UTC).isoformat()}

Features: {', '.join(features) if features else 'none'}"""

    subprocess.run(
        ["git", "add", str(asset_path)],
        check=True,
        capture_output=True
    )

    subprocess.run(
        ["git", "commit", "-m", message],
        check=True,
        capture_output=True
    )

# In Executor.execute(), add --commit-assets flag:
if config.commit_assets and result.success:
    _commit_generated_asset(result.output_path, metadata)
```

**CLI flag:** Add `--commit-assets` to `gen-media` command

## Quick Ramifications

- **Breaks anything?** No, all additive
- **Edge cases?** Git commit fails if repo has unstaged changes in unrelated files (should use `git add` on specific file only, as shown)
- **Constraints?** Increased verification time (~2-3 seconds for suggestion generation)

## Confidence

**Confidence: 75%** — Based on analysis of existing codebase (`executor.py`, `verification/` modules), user feedback patterns (you want actionable output, not raw scores), and Git being native to your workflow. Deduction for: uncertainty on whether you want generated assets committed by default (opt-in flag provided).

**Weakest assumption:** Recruiters care about structured regeneration suggestions. If wrong: they might only care about final score. Mitigation: make suggestions optional via `--verbose` flag or only show when score is below threshold.
