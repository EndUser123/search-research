#!/usr/bin/env python3
"""
Deterministic claim verifier — artifact-truth layer.

Fills the gap that unified_claim_verifier.py leaves: that module verifies
claims against SESSION tool_events (did you run a supporting tool). This one
verifies claims against the FILESYSTEM/REGISTRY directly (does the path exist,
is the module importable, is the symbol registered) and emits the RECEIPT —
the actual tool output — so the verdict is unfakeable.

Input  : claims.json  -> [{"id","claim","claim_type","evidence_source"}, ...]
Output : [{"id","claim","claim_type","verdict","receipt"}, ...]
         verdict in {PASS, FAIL, UNVERIFIABLE}
         UNVERIFIABLE = deterministic check not applicable -> route to LLM tier.

Claim types handled deterministically:
  existence      -> Path.exists / dir listing / find
  static-shape   -> read cited lines, return them as the receipt
  registered     -> grep settings.json + hook routers for the named hook
  importable     -> importlib check under the production sys.path
Others (behavior, non-code) -> UNVERIFIABLE.

Why receipts, not booleans: per "Tool Receipts, Not Zero-Knowledge Proofs"
(arXiv 2603.10060) — agents fabricate tool executions, so require the actual
output. A verdict without the receipt is just another claim.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HOOKS_ROOT = Path("P:/.claude/hooks")
SETTINGS_JSON = Path("P:/.claude/settings.json")

# Windows drive path  P:/...  or  C:\\...  ; unix absolute /a/b with a real separator chain.
# Single-segment tokens like /Write or /Edit are NOT paths -> require >=2 segments or a drive letter.
_PATH_RE = re.compile(
    r'(?:[A-Za-z]:[\\/][^\s"`\]\|<>]+|/[A-Za-z][^\s"`\]\|<>]*/[^\s"`\]\|<>]+)'
)
# backtick-quoted token that looks file-ish  `foo/bar.py`  `__lib/x`
_TICK_RE = re.compile(r"`([^\s`]+\.[a-z]{2,5}|[^\s`]*[\\/][^\s`]*)`")
# "lines 589-601" or "line 96"
_LINES_RE = re.compile(r"lines?\s*(\d+)(?:\s*[-–]\s*(\d+))?", re.IGNORECASE)

DETERMINISTIC_TYPES = {"existence", "static-shape", "registered", "importable"}


def _extract_paths(claim: str, evidence_source: str) -> list[str]:
    blob = f"{evidence_source}\n{claim}"
    found = set(_PATH_RE.findall(blob))
    for m in _TICK_RE.findall(blob):
        found.add(m)
    # normalize backslashes, strip trailing punctuation + a trailing :line or :lo-hi suffix
    out = []
    for p in found:
        p = p.rstrip(".,;)").strip("'\"")
        p = re.sub(r":\d+(?:-\d+)?$", "", p)  # "foo.py:280" / "foo.py:589-601" -> "foo.py"
        if len(p) < 3:
            continue
        out.append(p.replace("\\", "/"))
    return out


def _check_exists(path_str: str) -> dict[str, Any]:
    p = Path(path_str)
    if p.exists():
        if p.is_dir():
            try:
                children = sorted(c.name for c in p.iterdir())[:20]
            except OSError:
                children = []
            return {"exists": True, "kind": "dir", "sample": children}
        return {"exists": True, "kind": "file", "size": p.stat().st_size}
    # maybe the parent exists and the basename is missing -> name the real location
    for parent in [p.parent, p.parent.parent]:
        if parent.exists() and parent.is_dir():
            try:
                siblings = sorted(c.name for c in parent.iterdir())[:15]
            except OSError:
                siblings = []
            return {"exists": False, "checked": str(p), "nearest_dir": str(parent), "siblings": siblings}
    return {"exists": False, "checked": str(p)}


def _read_lines(path_str: str, lo: int, hi: int) -> dict[str, Any]:
    p = Path(path_str)
    if not p.exists():
        return {"readable": False, "reason": "path not found"}
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        return {"readable": False, "reason": str(e)}
    if lo > len(lines):
        # cited lines don't exist in the file -> claim about what's AT them is unconfirmable
        return {"readable": True, "in_range": False, "reason": "cited line range beyond file length", "file_lines": len(lines), "cited_from": lo}
    hi = min(hi, len(lines))
    lo = max(1, lo)
    snippet = {str(i): lines[i - 1] for i in range(lo, hi + 1)}
    return {"readable": True, "in_range": True, "file_lines": len(lines), "lines": snippet}


def _check_registered(name: str) -> dict[str, Any]:
    """Is `name` wired into the actual DISPATCH surface?

    Dispatch surface = settings.json + the known dispatch manifests (PreToolUse.py,
    Stop.py, hooks.json files, __lib/router.py). A name appearing only in __lib
    helpers, tests, or docs does NOT count as registered — that's a diagnostic
    mentioning the name, not a live dispatch entry. Returns UNVERIFIABLE in that
    case so the LLM tier can settle it rather than emitting a false PASS.
    """
    needle = name.strip("`'\"")
    dispatch_files = [
        SETTINGS_JSON,
        HOOKS_ROOT / "PreToolUse.py",
        HOOKS_ROOT / "Stop.py",
        HOOKS_ROOT / "Stop_router.py",
        HOOKS_ROOT / "UserPromptSubmit_router.py",
        HOOKS_ROOT / "PostToolUse_router.py",
    ]
    dispatch_hits: list[str] = []
    for t in dispatch_files:
        if t.exists() and t.is_file():
            try:
                if needle.lower() in t.read_text(encoding="utf-8", errors="replace").lower():
                    dispatch_hits.append(str(t))
            except OSError:
                pass
    # also scan hooks.json + router.py anywhere under hooks/ (plugin dispatch)
    try:
        r = subprocess.run(
            ["grep", "-rli", "--include=hooks.json", "--include=router.py", needle, str(HOOKS_ROOT)],
            capture_output=True, text=True, timeout=10,
        )
        dispatch_hits.extend(p for p in r.stdout.strip().splitlines() if p)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    if dispatch_hits:
        return {"registered": True, "dispatch_surface": dispatch_hits[:10]}

    # not in dispatch — but is it mentioned ANYWHERE (helpers/tests/docs)?
    nondispatch: list[str] = []
    try:
        r = subprocess.run(
            ["grep", "-rli", needle, str(HOOKS_ROOT)],
            capture_output=True, text=True, timeout=15,
        )
        nondispatch = r.stdout.strip().splitlines()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return {
        "registered": False,
        "dispatch_surface": [],
        "found_only_in_nondispatch": nondispatch[:10],
        "note": "name appears outside the dispatch surface; cannot confirm registration deterministically",
    }


def _check_importable(module_path: str) -> dict[str, Any]:
    """module_path may be a dotted name or a .py file."""
    if module_path.endswith(".py"):
        spec = importlib.util.spec_from_file_location("_probe", module_path)
        if spec is None or spec.loader is None:
            return {"importable": False, "reason": "no spec"}
        try:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            return {"importable": True}
        except Exception as e:
            return {"importable": False, "error": f"{type(e).__name__}: {e}"}
    try:
        importlib.import_module(module_path)
        return {"importable": True}
    except Exception as e:
        return {"importable": False, "error": f"{type(e).__name__}: {e}"}


def _classify_action(claim_type: str, evidence_source: str, claim: str) -> str:
    es = evidence_source.lower()
    cl = claim.lower()
    reg_signals = ("registered", "unregistered", "wired", "dispatch", "in settings.json", "in the router")
    if any(s in es or s in cl for s in reg_signals) or claim_type == "registered":
        return "registered"
    if "import" in es or "importable" in cl or claim_type == "importable":
        return "importable"
    if "line" in es:
        return "static-shape"
    return "exists"


def verify_claims(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for c in claims:
        cid = c.get("id", "?")
        claim = c.get("claim", "")
        ct = c.get("claim_type", "")
        es = c.get("evidence_source", "")
        rec: dict[str, Any] = {"id": cid, "claim": claim, "claim_type": ct}

        if ct not in DETERMINISTIC_TYPES:
            rec["verdict"] = "UNVERIFIABLE"
            rec["receipt"] = {"reason": f"claim_type={ct} not deterministic; route to LLM tier"}
            results.append(rec)
            continue

        action = _classify_action(ct, es, claim)
        paths = _extract_paths(claim, es)

        if action == "registered":
            # subject is the hook/module NAME, not settings.json. Prefer a backticked
            # name or a *.py stem from the claim; fall back to a path stem.
            subject = ""
            m = re.search(r"`([^`]+)`", claim)
            if m:
                subject = m.group(1)
            elif paths:
                subject = Path(paths[0]).name
            else:
                m2 = re.search(r"([\w\-]+\.py)", claim)
                subject = m2.group(1) if m2 else claim[:40]
            needle = subject[:-3] if subject.lower().endswith(".py") else subject
            rec["receipt"] = _check_registered(needle)
            # Registration receipts are boolean (in-dispatch: yes/no) but claim
            # polarity varies ("X is registered" vs "X is unregistered"). The
            # deterministic layer can't parse polarity reliably, so hand the rich
            # receipt to the LLM tier rather than guessing PASS/FAIL.
            rec["verdict"] = "UNVERIFIABLE"
            results.append(rec)
            continue
        elif action == "importable" and paths:
            rec["receipt"] = _check_importable(paths[0])
        elif action == "static-shape" and paths:
            lm = _LINES_RE.search(es)
            lo, hi = (int(lm.group(1)), int(lm.group(2) or lm.group(1))) if lm else (1, 40)
            rec["receipt"] = _read_lines(paths[0], lo, hi)
        elif paths:
            # existence — check every path found
            rec["receipt"] = {p: _check_exists(p) for p in paths[:5]}
        else:
            rec["verdict"] = "UNVERIFIABLE"
            rec["receipt"] = {"reason": "no path token extractable from claim/evidence"}
            results.append(rec)
            continue

        # derive verdict from receipt
        r = rec["receipt"]
        if isinstance(r, dict):
            # in_range=False (cited lines don't exist) is unconfirmable, not a pass
            if r.get("in_range") is False:
                rec["verdict"] = "UNVERIFIABLE"
            elif r.get("exists") is True or (r.get("readable") is True and r.get("in_range") is not False) or r.get("registered") is True or r.get("importable") is True:
                rec["verdict"] = "PASS"
            else:
                # multi-path existence receipt: {path: {exists: bool}, ...}
                child_results = [v for v in r.values() if isinstance(v, dict) and "exists" in v]
                if child_results:
                    exists_count = sum(1 for v in child_results if v.get("exists"))
                    if exists_count == len(child_results):
                        rec["verdict"] = "PASS"          # all exist
                    elif exists_count == 0:
                        rec["verdict"] = "FAIL"          # none exist
                    else:
                        rec["verdict"] = "UNVERIFIABLE"  # mixed — can't reduce to bool without parsing the claim's quantifier
                else:
                    rec["verdict"] = "FAIL"
        else:
            rec["verdict"] = "UNVERIFIABLE"
        results.append(rec)
    return results


def _self_check() -> None:
    """Reproduce-first: prove the verifier catches each known failure class."""
    cases = [
        # wrong path -> FAIL (the burn-class error this tool exists for)
        {"id": "BURN-1", "claim": "Stop_investigation_validator.py exists at the hooks root",
         "claim_type": "existence", "evidence_source": "P:/.claude/hooks/Stop_investigation_validator.py",
         "_expect": "FAIL"},
        # real path -> PASS
        {"id": "POS-1", "claim": "unified_claim_verifier.py exists",
         "claim_type": "existence", "evidence_source": "P:/.claude/hooks/unified_claim_verifier.py",
         "_expect": "PASS"},
        # path:line notation must not mangle the filename -> real file resolves -> PASS
        {"id": "PATHLINE-1", "claim": "verify_claims has a self-check",
         "claim_type": "static-shape", "evidence_source": "P:/.claude/hooks/scripts/verification/verify_claims.py:280",
         "_expect": "PASS"},
        # multi-path mixed (one real, one fake) -> UNVERIFIABLE, not PASS
        {"id": "MIXED-1", "claim": "both exist",
         "claim_type": "existence",
         "evidence_source": "P:/.claude/hooks/unified_claim_verifier.py and P:/.claude/hooks/NONEXISTENT_FAKE.py",
         "_expect": "UNVERIFIABLE"},
    ]
    results = {r["id"]: r for r in verify_claims(cases)}
    for c in cases:
        got = results[c["id"]]["verdict"]
        assert got == c["_expect"], f"{c['id']}: expected {c['_expect']}, got {got} — receipt={results[c['id']].get('receipt')}"
    print(f"self-check OK: {len(cases)} cases passed (FAIL/PASS/path:line/mixed all correct)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic claim verifier (artifact-truth layer).")
    ap.add_argument("claims_json", nargs="?", help="path to claims.json; omit to read stdin")
    ap.add_argument("--self-check", action="store_true", help="run reproduce-first self-test, then exit")
    ap.add_argument("--out", help="write results JSON here; default stdout")
    args = ap.parse_args()

    if args.self_check:
        _self_check()
        return 0

    raw = Path(args.claims_json).read_text(encoding="utf-8") if args.claims_json else sys.stdin.read()
    claims = json.loads(raw)
    results = verify_claims(claims)
    payload = json.dumps(results, indent=2, default=str)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
        print(f"wrote {len(results)} verdicts -> {args.out}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
