"""Tests for context_controller.render (pure markdown packet renderer).

Pure-function module: no I/O, no LLM calls. Tests verify packet shape,
truncation invariant, subagent advisory line, and phase banner.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Inject context_controller dir so `import render` / `import policy`
# resolve to the context_controller package.
_CONTEXT_CONTROLLER_DIR = str(Path(__file__).resolve().parent.parent / "context_controller")
if _CONTEXT_CONTROLLER_DIR not in sys.path:
    sys.path.insert(0, _CONTEXT_CONTROLLER_DIR)

import pytest

import render as render_mod
import policy as policy_mod
import state as state_mod

# Module-level imports
MAX_LIST_ITEMS = render_mod.MAX_LIST_ITEMS
MAX_PACKET_LINES = render_mod.MAX_PACKET_LINES
MAX_TEXT_CHARS = render_mod.MAX_TEXT_CHARS
RenderedPacket = render_mod.RenderedPacket
render_compact_packet = render_mod.render_compact_packet
render_phase_banner = render_mod.render_phase_banner

ContextHealth = state_mod.ContextHealth
classify_phase = policy_mod.classify_phase
evaluate_health = policy_mod.evaluate_health
recommend_subagent = policy_mod.recommend_subagent


# ---- Constants -------------------------------------------------------------


class TestRenderConstants:
    def test_max_packet_lines_is_bounded(self):
        # The plan's v1 contract caps packet length.
        assert 1 <= MAX_PACKET_LINES <= 100

    def test_max_list_items_bounded(self):
        assert 1 <= MAX_LIST_ITEMS <= 50

    def test_max_text_chars_bounded(self):
        assert 50 <= MAX_TEXT_CHARS <= 2000


# ---- render_phase_banner --------------------------------------------------


class TestRenderPhaseBanner:
    def test_none_input_returns_fallback(self):
        assert render_phase_banner(None) == "Phase: general"

    def test_known_classification(self):
        # The implementation regex requires a noun suffix (function, class, etc.)
        c = classify_phase("implement a new function for the test runner")
        assert render_phase_banner(c) == "Phase: implementation (rule: implement_verb)"

    def test_fallback_classification(self):
        c = classify_phase("hello world")
        assert render_phase_banner(c) == "Phase: general (rule: fallback)"

    def test_handoff_classification(self):
        c = classify_phase("hand off the rest")
        assert render_phase_banner(c) == "Phase: handoff (rule: handoff_keyword)"


# ---- render_compact_packet: empty inputs ---------------------------------


class TestRenderCompactPacketEmpty:
    def test_no_inputs_returns_minimal_packet(self):
        p = render_compact_packet()
        assert p.phase is None
        assert p.truncated is False
        # Must always include the title and phase banner
        assert "## Context Controller" in p.lines[0]
        assert any("Phase" in ln for ln in p.lines)

    def test_phase_only_echoes_phase(self):
        c = classify_phase("research how X works")
        p = render_compact_packet(classification=c)
        assert p.phase == "research"
        assert any("research" in ln for ln in p.lines)


# ---- render_compact_packet: phase + health ------------------------------


class TestRenderCompactPacketHealth:
    def test_compact_advisory_when_should_compact(self):
        c = classify_phase("implement a new function for the test runner")
        h = ContextHealth(large_outputs=3)
        a = evaluate_health(h, "implementation", None)
        p = render_compact_packet(classification=c, health_assessment=a)
        assert p.phase == "implementation"
        assert any("Compact recommended" in ln for ln in p.lines)

    def test_fresh_session_advisory(self):
        c = classify_phase("research X")
        h = ContextHealth(turn_count=10, phase_turns=0)
        a = evaluate_health(h, "research", "implementation")
        p = render_compact_packet(classification=c, health_assessment=a)
        assert any("Fresh session" in ln for ln in p.lines)

    def test_no_advisory_when_health_clean(self):
        c = classify_phase("implement X")
        h = ContextHealth()  # all zero
        a = evaluate_health(h, "general", None)
        p = render_compact_packet(classification=c, health_assessment=a)
        assert not any("Compact recommended" in ln for ln in p.lines)
        assert not any("Fresh session" in ln for ln in p.lines)


# ---- render_compact_packet: subagent advisory ----------------------------


class TestRenderCompactPacketSubagent:
    def test_subagent_advisory_line(self):
        c = classify_phase("investigate the bug")
        sub = recommend_subagent("investigate the bug")
        p = render_compact_packet(
            classification=c,
            subagent_recommended=sub,
        )
        assert any("Subagent delegation advisory" in ln for ln in p.lines)

    def test_no_subagent_advisory_when_false(self):
        c = classify_phase("implement X")
        p = render_compact_packet(
            classification=c,
            subagent_recommended=False,
        )
        assert not any("Subagent delegation advisory" in ln for ln in p.lines)

    def test_subagent_advisory_never_issues_dispatch_command(self):
        # The renderer must NEVER emit language like "dispatching" or
        # "sending to subagent" — the controller is advisory only.
        # The phrase "does not auto-dispatch" IS acceptable (it is the
        # advisory caveat, not a command).
        c = classify_phase("investigate deeply")
        p = render_compact_packet(
            classification=c,
            subagent_recommended=True,
        )
        joined = "\n".join(p.lines).lower()
        # "auto-dispatch" (the caveat) IS allowed.
        assert "auto-dispatch" in joined
        # But imperative dispatch commands must not appear.
        assert "dispatching" not in joined
        assert "sending" not in joined
        assert "we will dispatch" not in joined


# ---- render_compact_packet: envelope handling ----------------------------


class TestRenderCompactPacketEnvelope:
    def test_no_envelope_omits_section(self):
        p = render_compact_packet(envelope=None)
        assert not any("From prior session" in ln for ln in p.lines)

    def test_empty_envelope_omits_section(self):
        p = render_compact_packet(envelope={})
        assert not any("From prior session" in ln for ln in p.lines)

    def test_envelope_with_goal_emits_goal_line(self):
        env = {"resume_snapshot": {"goal": "Build X"}}
        p = render_compact_packet(envelope=env)
        assert any("Build X" in ln and "Goal" in ln for ln in p.lines)

    def test_envelope_with_active_files(self):
        env = {"resume_snapshot": {"active_files": ["a.py", "b.py", "c.py"]}}
        p = render_compact_packet(envelope=env)
        assert any("Active files" in ln for ln in p.lines)
        assert any("a.py" in ln for ln in p.lines)

    def test_envelope_active_files_capped(self):
        # More files than MAX_LIST_ITEMS → truncation.
        env = {"resume_snapshot": {
            "active_files": [f"file_{i}.py" for i in range(MAX_LIST_ITEMS * 3)]
        }}
        p = render_compact_packet(envelope=env)
        # Only the first MAX_LIST_ITEMS appear in lines.
        joined = "\n".join(p.lines)
        for i in range(MAX_LIST_ITEMS):
            assert f"file_{i}.py" in joined
        # Anything past the cap should NOT appear.
        assert f"file_{MAX_LIST_ITEMS}.py" not in joined

    def test_envelope_long_text_truncated(self):
        env = {"resume_snapshot": {"goal": "g" * (MAX_TEXT_CHARS * 3)}}
        p = render_compact_packet(envelope=env)
        joined = "\n".join(p.lines)
        # The ellipsis marker should be present on the truncated Goal line.
        assert "…" in joined
        # The full over-long string must NOT appear.
        assert ("g" * (MAX_TEXT_CHARS + 5)) not in joined

    def test_envelope_passed_through_verbatim(self):
        # The renderer is read-only against the envelope — no
        # rephrasing, no reformatting, no hallucination.
        env = {"resume_snapshot": {"goal": "exact text"}}
        p = render_compact_packet(envelope=env)
        assert any("exact text" in ln for ln in p.lines)


# ---- render_compact_packet: truncation ------------------------------------


class TestRenderCompactPacketTruncation:
    def test_oversized_envelope_is_truncated(self):
        # Build an envelope so large that the resulting packet
        # exceeds any reasonable max_lines.
        env = {"resume_snapshot": {
            "goal": "g" * 200,
            "current_task": "t" * 200,
            "next_step": "n" * 200,
            "active_files": [f"f{i}.py" for i in range(20)],
            "recent_decisions": [f"decision {i}" for i in range(20)],
            "blockers": [f"blocker {i}" for i in range(20)],
            "open_questions": [f"q{i}" for i in range(20)],
        }}
        p = render_compact_packet(envelope=env, max_lines=10)
        assert p.truncated is True
        assert len(p.lines) <= 10

    def test_under_limit_not_truncated(self):
        env = {"resume_snapshot": {"goal": "short"}}
        p = render_compact_packet(envelope=env, max_lines=MAX_PACKET_LINES)
        assert p.truncated is False

    def test_truncation_marker_on_last_line(self):
        env = {"resume_snapshot": {
            "goal": "g" * 5000,
            "active_files": [f"f{i}.py" for i in range(50)],
        }}
        p = render_compact_packet(envelope=env, max_lines=8)
        assert p.truncated is True
        # The last line should carry the truncation marker.
        assert "truncated" in p.lines[-1].lower()

    def test_max_lines_zero_falls_back_to_default(self):
        # Invalid max_lines → silently use default.
        p = render_compact_packet(max_lines=0)
        assert len(p.lines) <= MAX_PACKET_LINES

    def test_max_lines_negative_falls_back_to_default(self):
        p = render_compact_packet(max_lines=-5)
        assert len(p.lines) <= MAX_PACKET_LINES

    def test_max_lines_non_int_falls_back_to_default(self):
        p = render_compact_packet(max_lines="oops")  # type: ignore[arg-type]
        assert len(p.lines) <= MAX_PACKET_LINES


# ---- RenderedPacket dataclass --------------------------------------------


class TestRenderedPacket:
    def test_construction(self):
        p = RenderedPacket(
            lines=("line1", "line2"),
            truncated=False,
            phase="research",
        )
        assert p.lines == ("line1", "line2")
        assert p.truncated is False
        assert p.phase == "research"

    def test_frozen(self):
        p = RenderedPacket(lines=(), truncated=False, phase=None)
        with pytest.raises(Exception):
            p.phase = "research"  # type: ignore[misc]

    def test_lines_is_tuple(self):
        p = render_compact_packet()
        assert isinstance(p.lines, tuple)


# ---- Determinism --------------------------------------------------------


class TestRenderDeterminism:
    def test_same_inputs_same_packet(self):
        env = {"resume_snapshot": {"goal": "Build X"}}
        c = classify_phase("implement Y")
        a = evaluate_health(ContextHealth(large_outputs=2), "implementation", None)
        p1 = render_compact_packet(
            envelope=env, classification=c, health_assessment=a, subagent_recommended=True
        )
        p2 = render_compact_packet(
            envelope=env, classification=c, health_assessment=a, subagent_recommended=True
        )
        assert p1.lines == p2.lines
        assert p1.phase == p2.phase
        assert p1.truncated == p2.truncated
