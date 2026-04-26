from __future__ import annotations


def classify_freshness(
    *,
    artifact_git_sha: str | None,
    current_git_sha: str | None,
    artifact_target: str | None,
    current_target: str | None,
) -> str:
    if artifact_target and current_target and artifact_target != current_target:
        return "stale-target"
    if artifact_git_sha and current_git_sha and artifact_git_sha != current_git_sha:
        return "stale-git"
    if artifact_target and current_target and artifact_target == current_target:
        return "fresh"
    return "unknown"
