import copy
import math

import numpy as np
import pytest

from tools.qhtri_spinor_lift_v01 import (
    QhtriSpinorLiftError,
    build_spinor_lift_receipt,
    exact_increment_step,
    predicted_projected_step,
    validate_spinor_lift_receipt,
)


def test_two_pi_toggles_spinor_sheet_and_four_pi_restores_it():
    phase = np.zeros(36)
    turns = np.zeros(36, dtype=np.int64)

    two_pi = exact_increment_step(phase, turns, np.full(36, 2.0 * math.pi))
    assert set(two_pi.turns) == {1}
    assert set(two_pi.sheet) == {-1}

    four_pi = exact_increment_step(phase, turns, np.full(36, 4.0 * math.pi))
    assert set(four_pi.turns) == {2}
    assert set(four_pi.sheet) == {1}


def test_negative_winding_has_same_z2_parity_rule():
    phase = np.zeros(36)
    turns = np.zeros(36, dtype=np.int64)

    minus_two_pi = exact_increment_step(phase, turns, np.full(36, -2.0 * math.pi))
    assert set(minus_two_pi.turns) == {-1}
    assert set(minus_two_pi.sheet) == {-1}

    minus_four_pi = exact_increment_step(phase, turns, np.full(36, -4.0 * math.pi))
    assert set(minus_four_pi.turns) == {-2}
    assert set(minus_four_pi.sheet) == {1}


def test_multiple_exact_steps_accumulate_integer_lift():
    phase = np.zeros(36)
    turns = np.zeros(36, dtype=np.int64)
    first = exact_increment_step(phase, turns, np.full(36, 1.5 * math.pi))
    second = exact_increment_step(first.projected_phase, first.turns, np.full(36, 1.5 * math.pi))
    assert set(second.turns) == {1}
    assert set(second.sheet) == {-1}
    assert set(np.round(second.projected_phase, 12)) == {round(math.pi, 12)}


def test_prediction_selects_same_lift_for_equivalent_projective_representatives():
    before = np.zeros(36)
    turns = np.zeros(36, dtype=np.int64)
    increment = np.full(36, 2.0 * math.pi + 0.25)

    canonical = predicted_projected_step(before, turns, increment, np.full(36, 0.25))
    shifted = predicted_projected_step(before, turns, increment, np.full(36, 0.25 + 2.0 * math.pi))
    assert canonical.turns == shifted.turns
    assert canonical.sheet == shifted.sheet
    assert set(canonical.turns) == {1}


def test_prediction_fails_closed_at_exact_half_turn_ambiguity():
    with pytest.raises(QhtriSpinorLiftError, match="ambiguous"):
        predicted_projected_step(
            np.zeros(36),
            np.zeros(36, dtype=np.int64),
            np.full(36, math.pi),
            np.zeros(36),
        )


def test_receipt_roundtrip_and_tamper_detection():
    step = exact_increment_step(np.zeros(36), np.zeros(36, dtype=np.int64), np.full(36, 2.0 * math.pi))
    receipt = build_spinor_lift_receipt(
        qhtri_tick=17,
        projective_state_commitment="11" * 32,
        generator_commitment="22" * 32,
        step=step,
        source_evidence_ref="shadow:/dev/shm/ciel_noema/z2_candidate",
    )
    validate_spinor_lift_receipt(receipt)
    assert set(receipt["spinor_sheet"]) == {-1}

    tampered = copy.deepcopy(receipt)
    tampered["turns"][0] += 1
    with pytest.raises(QhtriSpinorLiftError):
        validate_spinor_lift_receipt(tampered)
