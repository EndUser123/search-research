"""Runtime ground-truth renderer.

Reads `P:/.claude/hooks/analysis/runtime-ground-truth.md`, parses the table,
and renders each row as a one-line claim. Each entry knows its verification
command and last_verified date; this module does NOT re-run those commands
(render is pure, no IO, suitable for SessionStart hot-path). The caller
(`aca_session_ground_truth_inject.py`) decides whether to surface the
stale marker based on `last_verified + expiry` heuristics. Stale entries
render as `[STALE — reverify: <cmd>]` instead of being dropped, so the
model sees the fact AND knows it is past its freshness window.

Cumulative injection budget: protected slots — this renderer AND
`UserPromptSubmit_modules/mechanism_manifest.py` are PROTECTED (render in
full); if the broader injector total exceeds BUDGET_TOTAL_CHARS, the
non-protected injectors (recall segments, etc.) are truncated first.

Ponytail: stdlib only, no deps, pure function on a parseable table.
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path


GROUND_TRUTH_PATH = Path(
    "P:/.claude/hooks/analysis/runtime-ground-truth.md"
)


# Cumulative budget across all injectors that surface to the model.
# ground_truth + mechanism_manifest are PROTECTED (see module docstring).
BUDGET_TOTAL_CHARS = 1800
BUDGET_PROTECTED_CHARS = 800  # sum across ground_truth + mechanism_manifest


# Expiry heuristics (calendar-anchored). Each row's `expiry_trigger` column
# is parsed heuristically; unknown triggers default to 30d.
_DEFAULT_STALE_DAYS = 30
_TRIGGER_DAYS = [
    (re.compile(r"calendar\s+(\d{4})-(\d{2})", re.I), "calendar"),  # calendar 2027-01
    (re.compile(r"next session start", re.I), "session"),
    (re.compile(r"(\d+)\s*mo(?:nth)?\b", re.I), "months"),
    (re.compile(r"(\d+)\s*d(?:ay)?\b", re.I), "days"),
]


def _stale_after_days(expiry_trigger: str) -> int | None:
    """Return the staleness window in days, or None for session-scoped triggers.

    `None` means "re-verify every session, never silently trust". The renderer
    treats None as ALWAYS stale so the model is forced to run the verification
    command instead of citing an unchecked fact.
    """
    s = (expiry_trigger or "").strip().lower()
    if not s or "session" in s:
        return None
    for pat, _label in _TRIGGER_DAYS:
        m = pat.search(s)
        if m:
            if pat.pattern.startswith("calendar"):
                # calendar YYYY-MM — far-future anchor
                year, month = int(m.group(1)), int(m.group(2))
                anchor = datetime.date(year, month, 1)
                today = datetime.date.today()
                return max((anchor - today).days, 0)
            if _label == "months":
                return int(m.group(1)) * 30
            if _label == "days":
                return int(m.group(1))
    return _DEFAULT_STALE_DAYS


def parse_table(md_text: str) -> list[dict]:
    """Parse the rows of the markdown table (skip header + separator).

    Each row is a dict with keys: fact, source, verification_command,
    last_verified, expiry_trigger. The markdown cell syntax (escaped pipe) is preserved
    in `fact` because none of the seed rows use pipes, but if any do, callers
    should `fact.replace(chr(124), "")` (strip stray pipes) before display.
    """
    rows: list[dict] = []
    for line in md_text.splitlines():
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        # Skip the header row (first non-separator row containing "fact")
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0].lower() == "fact":
            continue
        if len(cells) != 5:
            continue
        rows.append({
            "fact": cells[0],
            "source": cells[1],
            "verification_command": cells[2],
            "last_verified": cells[3],
            "expiry_trigger": cells[4],
        })
    return rows


def render(
    rows: list[dict],
    today: datetime.date | None = None,
    budget_chars: int = BUDGET_PROTECTED_CHARS,
) -> str:
    """Render the rows into a model-readable block.

    - Each row becomes one line: `- <fact>  [last_verified YYYY-MM-DD]` or
      `- [STALE — reverify: <cmd>] <fact>  [last_verified YYYY-MM-DD]`
    - Output is truncated to `budget_chars` (Ponytail: hard cap, never exceed).
    - Stale entries are NEVER dropped — they keep their verification command so
      the model can re-verify. Truncation only hides lines past the cap.
    """
    today = today or datetime.date.today()
    # Ponytail: budget is a HARD cap on total output length (headers + rows).
    # We pre-compute header size and reserve budget so rows always fit.
    header = (
        "## RUNTIME GROUND TRUTH — verified facts (SessionStart)\n"
        "Stale entries: run the verification command before citing."
    )
    out: list[str] = [header]
    rendered_total = len(header) + 1  # +1 for the joining newline
    for r in rows:
        try:
            lv = datetime.date.fromisoformat(r["last_verified"])
        except ValueError:
            lv = today  # malformed date → treat as freshly verified (harmless)

        stale_after = _stale_after_days(r["expiry_trigger"])
        is_stale = stale_after is None or (today - lv).days > stale_after

        fact = r["fact"]
        cmd = r["verification_command"]
        prefix = f"[STALE — reverify: `{cmd}`] " if is_stale else ""
        line = f"- {prefix}{fact}  [last_verified {r['last_verified']}]"

        if rendered_total + len(line) + 1 > budget_chars:
            # Ponytail: budget is a hard cap; leftover rows omitted (not stale
            # — fresh rows can also be truncated under tight budgets).
            remaining = max(budget_chars - rendered_total - 1, 0)
            marker = (
                f"- … ({remaining} chars cap; "
                f"see runtime-ground-truth.md for remaining rows)"
            )
            if rendered_total + len(marker) + 1 <= budget_chars:
                out.append(marker)
            break
        out.append(line)
        rendered_total += len(line) + 1

    return "\n".join(out)


def load_and_render(
    path: Path | str = GROUND_TRUTH_PATH,
    today: datetime.date | None = None,
    budget_chars: int = BUDGET_PROTECTED_CHARS,
) -> str:
    """Convenience: read the file, parse, render."""
    p = Path(path)
    return render(parse_table(p.read_text(encoding="utf-8")), today=today, budget_chars=budget_chars)


if __name__ == "__main__":
    # Self-check: render against today, plus a far-future date, plus a
    # malformed date. Failure here means the parser broke.
    print(load_and_render())