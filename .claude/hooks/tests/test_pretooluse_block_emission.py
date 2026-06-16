#!/usr/bin/env python3
"""Invariant: every PreToolUse block emission carries the reason for the model.

Root-cause regression guard. Three independent ``print(json.dumps(...))`` block
emission sites in ``PreToolUse.py`` drifted apart, and one (the malformed-modify
fallback) emitted the legacy ``{"decision":"block","reason":...}`` shape with no
``hookSpecificOutput.permissionDecisionReason``. Claude Code renders that shape
as a generic "denied this tool", dropping the gate's fix instruction (e.g.
"call Skill() first"). The model never sees why it was blocked.

This test enforces the invariant structurally so a NEW emission site cannot
silently reintroduce the opaque-message bug. It parses the AST of PreToolUse.py
and asserts that every ``json.dumps(...)`` argument that constructs a
``decision: block`` payload either:
  - is a call to the single choke-point helper ``_block_payload(...)``, or
  - is a name bound to ``_block_payload(...)`` earlier in the same function, or
  - is a dict literal that itself contains a ``hookSpecificOutput`` key.

Any other block emission shape fails the test.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

PRETOOLUSE = Path(__file__).resolve().parents[1] / "PreToolUse.py"


def _load_tree() -> tuple[ast.Module, str]:
    src = PRETOOLUSE.read_text(encoding="utf-8")
    return ast.parse(src), src


def _dumps_calls(tree: ast.Module):
    """Yield every json.dumps(arg) Call node."""
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "dumps"
            and node.args
        ):
            yield node


def _names_bound_to_block_payload(tree: ast.Module) -> set[str]:
    """Names assigned the result of _block_payload(...) anywhere in the module."""
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            fn = node.value.func
            if isinstance(fn, ast.Name) and fn.id == "_block_payload":
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        bound.add(tgt.id)
    return bound


def _is_block_dict_literal(arg: ast.AST) -> bool:
    """True if arg is a dict literal with a 'decision': 'block' entry."""
    if not isinstance(arg, ast.Dict):
        return False
    for k, v in zip(arg.keys, arg.values):
        if (
            isinstance(k, ast.Constant)
            and k.value == "decision"
            and isinstance(v, ast.Constant)
            and v.value == "block"
        ):
            return True
    return False


def _dict_has_hook_specific_output(arg: ast.Dict) -> bool:
    return any(
        isinstance(k, ast.Constant) and k.value == "hookSpecificOutput"
        for k in arg.keys
    )


def test_choke_point_helper_exists():
    """The single block-emission helper must exist and attach permissionDecisionReason."""
    tree, src = _load_tree()
    fn = next(
        (
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == "_block_payload"
        ),
        None,
    )
    assert fn is not None, "_block_payload choke-point helper is missing"
    body_src = ast.get_source_segment(src, fn) or ""
    assert "permissionDecisionReason" in body_src, (
        "_block_payload must attach permissionDecisionReason"
    )
    assert "permissionDecision" in body_src and "deny" in body_src


def test_every_block_emission_carries_reason():
    """No block emission may use the legacy bare {decision: block, reason} shape."""
    tree, _ = _load_tree()
    bound_names = _names_bound_to_block_payload(tree)

    offenders: list[str] = []
    for call in _dumps_calls(tree):
        arg = call.args[0]

        # OK: direct helper call -> json.dumps(_block_payload(...))
        if (
            isinstance(arg, ast.Call)
            and isinstance(arg.func, ast.Name)
            and arg.func.id == "_block_payload"
        ):
            continue

        # OK: a name bound to _block_payload(...) -> response/block_response
        if isinstance(arg, ast.Name) and arg.id in bound_names:
            continue

        # Only scrutinize args that actually build a block payload
        if _is_block_dict_literal(arg):
            if isinstance(arg, ast.Dict) and _dict_has_hook_specific_output(arg):
                continue
            offenders.append(
                f"L{call.lineno}: bare block dict literal without hookSpecificOutput"
            )

    assert not offenders, (
        "Block emissions must carry permissionDecisionReason "
        "(route through _block_payload). Offending sites:\n  "
        + "\n  ".join(offenders)
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
