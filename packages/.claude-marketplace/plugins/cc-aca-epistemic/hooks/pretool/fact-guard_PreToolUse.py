#!/usr/bin/env python3
"""PreToolUse hook: Block unsupported literals and contamination in structured edits.

Input: JSON on stdin with tool_name, tool_input fields.
Output: exit 0 (allow) or exit 2 (block) with reason on stderr.
"""
from __future__ import annotations



# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P

def _normalize_stdout(data: dict) -> dict:
    """Normalize hook output to Claude Code Zod-valid schema."""
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data


_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import json
import subprocess
import sys
from pathlib import Path

# Add src to path

from state import detect_terminal_id, read_state
from file_patterns import is_structured_file, extract_facts_from_content
from contamination import detect_contamination
from provenance import record_edit_provenance



def _get_exempt_facts(target_file: str) -> set:
    """Read exempt_facts from the active skill's SKILL.md frontmatter.
    
    Returns a set of "entity.field" strings that are exempt from provenance checking.
    """
    import re
    try:
        skill_dir = None
        # Walk up from target file to find a SKILL.md
        fpath = Path(target_file).resolve()
        for parent in fpath.parents:
            skill_md = parent / "SKILL.md"
            if skill_md.exists():
                skill_dir = parent
                break
        if not skill_dir:
            return set()
        
        # Read frontmatter
        text = skill_dir.joinpath("SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        if not match:
            return set()
        
        # Parse exempt_facts list
        exempt = set()
        for line in match.group(1).splitlines():
            if line.startswith("exempt_facts:"):
                # Collect list items (may span multiple lines)
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

        # Extract target file path
        if isinstance(tool_input, dict):
            target_file = tool_input.get("file_path") or tool_input.get("path") or ""
        elif isinstance(tool_input, str):
            target_file = tool_input.split()[0] if tool_input else ""
        else:
            target_file = ""

        if not target_file or not is_structured_file(target_file):
            sys.exit(0)

        # Extract proposed content
        proposed_content = tool_input.get("content", "") if isinstance(tool_input, dict) else ""
        if tool_name in ("Edit", "edit_file") and isinstance(tool_input, dict):
            proposed_content = tool_input.get("new_string", "")

        if not proposed_content:
            sys.exit(0)

        proposed_facts = extract_facts_from_content(proposed_content, target_file)
        if not proposed_facts:
            sys.exit(0)

        # Get observed facts
        terminal_id = detect_terminal_id()
        observations = read_state("observed_facts.json", terminal_id)
        observed_list = observations.get("facts", []) if isinstance(observations, dict) else []

        # Read existing file content
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                existing_content = f.read()
        except FileNotFoundError:
            existing_content = ""

        # Check for contamination
        contamination_hits = detect_contamination(proposed_facts, existing_content, observed_list)

        if contamination_hits:
            # Call M2.7 verifier for confirmation
            verified_blocks = _call_m2_7_verifier(
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

        # Check for unsupported concrete values (no provenance, not contamination, not placeholder)
        # Skip exempt entity.field pairs per active skill's exempt_facts frontmatter
        exempt_facts = _get_exempt_facts(target_file)
        for proposed in proposed_facts:
            ef = f"{proposed.get("entity")}.{proposed.get("field")}"
            if ef in exempt_facts:
                continue
            value = proposed.get("value", "")
            if value.lower() not in ("none", "null", "unknown", "todo", "n/a", ""):
                has_provenance = any(
                    obs.get("entity") == proposed.get("entity")
                    and obs.get("field") == proposed.get("field")
                    and obs.get("value") == value
                    for obs in observed_list
                )
                if not has_provenance:
                    reason = (
                        f"Unsupported literal: {proposed.get('entity')}.{proposed.get('field')} "
                        f"= {value} (no evidence in session)"
                    )
                    record_edit_provenance(target_file, False, reason, terminal_id)
                    print(json.dumps({"decision": "block", "reason": reason}), file=sys.stderr)
                    sys.exit(2)

        # All checks passed
        record_edit_provenance(target_file, True, "provenance verified", terminal_id)
        sys.exit(0)

    except PermissionError as e:
        print(json.dumps({"error": f"Permission denied: {e}"}), file=sys.stderr)
        sys.exit(2)
    except OSError as e:
        print(json.dumps({"error": f"OS error: {e}"}), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(json.dumps({"error": f"PreToolUse error: {e}"}), file=sys.stderr)
        sys.exit(2)


def _call_m2_7_verifier(
    target_file: str,
    proposed_facts: list,
    contamination_hits: list,
    terminal_id: str,
) -> list:
    """Call ai-pcli M2.7 to verify contamination risk.

    Conservative: if verifier fails, don't block (prefer false negatives during pilot).
    """
    try:
        payload = {
            "task": "verify_provenance",
            "file": target_file,
            "proposed_facts": proposed_facts,
            "contamination_hits": contamination_hits,
        }

        prompt = (
            "You are a provenance verifier. Given a proposed edit to a structured file, "
            "determine if the contamination is real.\n\n"
            f"File: {target_file}\n"
            f"Proposed facts:\n{json.dumps(proposed_facts, indent=2)}\n\n"
            f"Potential contamination (value copied from neighbor):\n"
            f"{json.dumps(contamination_hits, indent=2)}\n\n"
            "Is this likely adjacent-entry contamination (value copied from a neighbor "
            "without entity-specific evidence)?\n"
            'Respond ONLY with JSON:\n'
            '{"contamination_confirmed": true|false, "confidence": 0.0-1.0, "reason": "..."}'
        )

        result = subprocess.run(
            ["ai-pcli", "m2.7", "--model", "minimax-m2.7", "--json-mode", prompt],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            try:
                response = json.loads(result.stdout)
                if response.get("contamination_confirmed") and response.get("confidence", 0) > 0.7:
                    return contamination_hits
            except json.JSONDecodeError:
                pass

        return []

    except Exception:
        return []


if __name__ == "__main__":
    main()
