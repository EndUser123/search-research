#!/usr/bin/env python3
"""PreToolUse hook: Block unsupported literals and contamination in structured edits.

Input: JSON on stdin with tool_name, tool_input fields.
Output: exit 0 (allow) or exit 2 (block) with reason on stderr.
"""
from __future__ import annotations

import json
import os


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---




# --- plugin bootstrap ---
import sys
from pathlib import Path


def _load_minimax_key() -> str | None:
    key = os.environ.get("MINIMAX_API_KEY", "").strip().strip('"')
    if key:
        return key
    env_path = Path("P:/.env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("MINIMAX_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


def _load_mistral_key() -> str | None:
    key = os.environ.get("MISTRAL_API_KEY", "").strip().strip('"')
    if key:
        return key
    env_path = Path("P:/.env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("MISTRAL_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


def _get_exempt_facts(target_file: str) -> set:
    """Read exempt_facts from the active skill SKILL.md frontmatter.

    Returns a set of "entity.field" strings that are exempt from provenance checking.
    """
    import re
    try:
        skill_dir = None
        fpath = Path(target_file).resolve()
        for parent in fpath.parents:
            skill_md = parent / "SKILL.md"
            if skill_md.exists():
                skill_dir = parent
                break
        if not skill_dir:
            return set()

        text = skill_dir.joinpath("SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if not match:
            return set()

        exempt = set()
        for line in match.group(1).splitlines():
            if line.startswith("exempt_facts:"):
                rest = line[14:].strip()
                if rest.startswith("["):
                    rest = rest[1:]
                if rest.endswith("]"):
                    rest = rest[:-1]
                for item in rest.split(","):
                    item = item.strip().strip("'\"").strip()
                    if item:
                        exempt.add(item)
                break
        return exempt
    except Exception:
        return set()



def main() -> None:
    try:
        hook_input = json.load(sys.stdin)

        tool_name = hook_input.get("tool_name", "")
        tool_input = hook_input.get("tool_input", "")

        if tool_name not in ("Write", "Edit", "MultiEdit", "write_file", "edit_file", "multi_edit"):
            sys.exit(0)

        if isinstance(tool_input, dict):
            target_file = tool_input.get("file_path") or tool_input.get("path") or ""
        elif isinstance(tool_input, str):
            target_file = tool_input.split()[0] if tool_input else ""
        else:
            target_file = ""

        if not target_file or not is_structured_file(target_file):
            sys.exit(0)

        proposed_content = tool_input.get("content", "") if isinstance(tool_input, dict) else ""
        if tool_name in ("Edit", "edit_file") and isinstance(tool_input, dict):
            proposed_content = tool_input.get("new_string", "")

        if not proposed_content:
            sys.exit(0)

        proposed_facts = extract_facts_from_content(proposed_content, target_file)
        if not proposed_facts:
            sys.exit(0)

        terminal_id = detect_terminal_id()
        observations = read_state("observed_facts.json", terminal_id)
        observed_list = observations.get("facts", []) if isinstance(observations, dict) else []

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                existing_content = f.read()
        except FileNotFoundError:
            existing_content = ""

        contamination_hits = detect_contamination(proposed_facts, existing_content, observed_list)

        if contamination_hits:
            # Dual-LLM verification (MiniMax + Mistral parallel)
            verified_blocks = _call_dual_llm_verifier(
                target_file, proposed_facts, contamination_hits, terminal_id
            )

            if verified_blocks:
                hit = verified_blocks[0]
                reason = (
                    f"Adjacent-entry contamination detected: "
                    f"{hit.get('field')} value '{hit.get('value')}' "
                    f"copied from {hit.get('matched_entity_a')} "
                    f"(similarity: {hit.get('similarity', 'N/A')})"
                )
                record_edit_provenance(target_file, False, reason, terminal_id)
                print(json.dumps({"decision": "block", "reason": reason}), file=sys.stderr)
                sys.exit(2)

        # Check for unsupported concrete values
        exempt_facts = _get_exempt_facts(target_file)
        for proposed in proposed_facts:
            entity = proposed.get("entity", "")
            field = proposed.get("field", "")
            ef = f"{entity}.{field}"
            if ef in exempt_facts:
                continue
            value = proposed.get("value", "")
            if value.lower() not in ("none", "null", "unknown", "todo", "n/a", ""):
                has_provenance = any(
                    obs.get("entity") == entity
                    and obs.get("field") == field
                    and obs.get("value") == value
                    for obs in observed_list
                )
                if not has_provenance:
                    reason = (
                        f"Unsupported literal: {entity}.{field} "
                        f"= {value} (no evidence in session)"
                    )
                    record_edit_provenance(target_file, False, reason, terminal_id)
                    print(json.dumps({"decision": "block", "reason": reason}), file=sys.stderr)
                    sys.exit(2)

        record_edit_provenance(target_file, True, "provenance verified", terminal_id)
        sys.exit(0)

    except PermissionError as e:
        _fail_open("PermissionError", e)
    except OSError as e:
        _fail_open("OSError", e)
    except Exception as e:
        _fail_open("Exception", e)


def _fail_open(error_class: str, exc: BaseException) -> None:
    """Convert a runtime crash into fail-OPEN with a dead-gate alarm.

    Previously these three except blocks all called sys.exit(2), which the
    epistemic router (router.py:107) propagates as a hard block. An internal
    bug in fact-guard (a permission error reading a file, an OOM, anything)
    was indistinguishable from an intentional block. Same fail-closed hazard
    we fixed in PreToolUse_investigation_gate last session.

    Now: log the fault to gate_faults.jsonl (surfaced at next SessionStart),
    print an approve JSON, exit 0. The model keeps working; the human sees
    the alarm on the next session.
    # ponytail: ceiling — if the alarm itself fails, it must never become a
    # new fault source. Hence the try/except wrapping the record_fault call.
    """
    try:
        from pathlib import Path as _P
        import sys as _sys
        _candidate = _P("P:/.claude/hooks/__lib")
        if _candidate.exists() and str(_candidate) not in _sys.path:
            _sys.path.insert(0, str(_candidate))
        from gate_health import record_fault  # type: ignore
        record_fault(
            "PreToolUse",
            "fact-guard_PreToolUse",
            f"{error_class}: {type(exc).__name__}: {exc}",
        )
    except Exception:
        pass  # alarm failure must never block the fail-open
    print(json.dumps({"decision": "approve", "reason": "fact-guard: internal error, fail-open"}))
    sys.exit(0)


# =============================================================================
# Dual-LLM contamination verifier - MiniMax + Mistral parallel
# =============================================================================


def _build_verifier_prompt(
    target_file: str,
    proposed_facts: list,
    contamination_hits: list,
) -> str:
    """Build the user prompt for the contamination verifier."""
    return (
        f"File: {target_file}\n"
        f"Proposed facts:\n{json.dumps(proposed_facts, indent=2)}\n\n"
        f"Potential contamination (value copied from neighbor):\n"
        f"{json.dumps(contamination_hits, indent=2)}\n\n"
        "Is this likely adjacent-entry contamination (value copied from a neighbor "
        "without entity-specific evidence)?"
    )


def _parse_verifier_response(raw_text: str) -> dict | None:
    """Parse JSON response from verifier LLM. Returns dict or None on failure."""
    try:
        text = raw_text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines).strip()
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def _call_minimax_verifier(user_prompt: str) -> dict | None:
    """Call MiniMax API for contamination verification.

    Returns parsed JSON response or None on any failure (fail-open).
    """
    api_key = _load_minimax_key()
    if not api_key:
        return None

    try:
        resp = requests.post(
            "https://api.minimax.io/anthropic/v1/messages",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": MINIMAX_MODEL,
                "max_tokens": 1024,
                "system": VERIFIER_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": user_prompt}],
            },
            timeout=VERIFIER_TIMEOUT_SEC,
        )

        if resp.status_code != 200:
            return None

        data = resp.json()
        raw_text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                raw_text += block.get("text", "")
        raw_text = raw_text.strip()

        if not raw_text:
            return None

        return _parse_verifier_response(raw_text)

    except requests.Timeout:
        return None
    except Exception:
        return None


def _call_mistral_verifier(user_prompt: str) -> dict | None:
    """Call Mistral API for contamination verification.

    Returns parsed JSON response or None on any failure (fail-open).
    """
    api_key = _load_mistral_key()
    if not api_key:
        return None

    try:
        from mistralai.client import Mistral

        client = Mistral(api_key=api_key)
        response = client.chat.complete(
            model=MISTRAL_MODEL,
            messages=[
                {"role": "system", "content": VERIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            reasoning_effort="high",
            timeout_ms=VERIFIER_TIMEOUT_SEC * 1000,
        )

        if not response or not response.choices:
            return None

        raw_text = response.choices[0].message.content
        if not raw_text:
            return None

        return _parse_verifier_response(raw_text.strip())

    except Exception:
        return None


def _call_dual_llm_verifier(
    target_file: str,
    proposed_facts: list,
    contamination_hits: list,
    terminal_id: str,
) -> list:
    """Call MiniMax + Mistral in parallel to verify contamination.

    Conservative merge: if EITHER model confirms contamination with
    confidence > 0.7, treat it as confirmed.

    Safeguards:
    1. Fail-open: any error returns [] (never blocks on LLM failure)
    2. Per-session cap: max VERIFIER_CAP calls before auto-skip
    3. Hard timeout: VERIFIER_TIMEOUT_SEC per call
    4. Parallel execution: zero extra latency vs single-model
    """
    count = _VERIFIER_COUNTS.get(terminal_id, 0)
    if count >= VERIFIER_CAP:
        return []
    _VERIFIER_COUNTS[terminal_id] = count + 1

    user_prompt = _build_verifier_prompt(target_file, proposed_facts, contamination_hits)

    try:
        minimax_result: dict | None = None
        mistral_result: dict | None = None

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(_call_minimax_verifier, user_prompt): "minimax",
                executor.submit(_call_mistral_verifier, user_prompt): "mistral",
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                    if name == "minimax":
                        minimax_result = result
                    else:
                        mistral_result = result
                except Exception:
                    pass

        def _is_confirmed(r: dict | None) -> bool:
            if r is None:
                return False
            return (
                r.get("contamination_confirmed") is True
                and r.get("confidence", 0) > 0.7
            )

        if _is_confirmed(minimax_result) or _is_confirmed(mistral_result):
            return contamination_hits

        return []

    except Exception:
        return []


if __name__ == "__main__":
    main()
