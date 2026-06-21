"""Regression: EpistemicConfig must not be constructed with sectional_response_required.

The field is a dynamic attribute read via getattr in epistemic_validator, NOT an
__init__ field. Passing it as a kwarg raised TypeError, which _run_epistemic_contract
swallowed -> the gate ran dead. See Stop.py final-answer branch.
"""
import sys

sys.path.insert(0, "P:/.claude/hooks")

from epistemic_validator import EpistemicConfig, validate


def test_sectional_attr_set_dynamically_not_via_init():
    # __init__ rejects it (the bug was passing it as a kwarg)
    try:
        EpistemicConfig(sectional_response_required=True)
        raise AssertionError("expected TypeError for unknown kwarg")
    except TypeError:
        pass

    # but it works as a dynamic attribute, which is how Stop.py now sets it
    cfg = EpistemicConfig(mode="warn", turn_mode="final-answer")
    cfg.sectional_response_required = True
    assert getattr(cfg, "sectional_response_required", False) is True
    # validate runs without throwing on a config carrying the dynamic attr
    validate("[FACT] x\n[INFERENCE] y\n[UNKNOWN] z\n[RECOMMENDATION] w", cfg)


if __name__ == "__main__":
    test_sectional_attr_set_dynamically_not_via_init()
    print("PASS")
