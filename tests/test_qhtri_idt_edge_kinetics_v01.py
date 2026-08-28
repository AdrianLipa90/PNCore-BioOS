import copy
import math

import pytest

from tools.qhtri_idt_edge_kinetics_v01 import (
    QhtriIdtEdgeKineticsError,
    build_edge_kinetics_receipt,
    edge_kinetics_from_qhtri,
    validate_edge_kinetics_receipt,
    validate_edge_reversal,
)


def test_reversal_and_idt_roundtrip_on_deterministic_grid():
    cases = 0
    for coupling in (-0.9, -0.25, 0.1, 0.73):
        for phi_i in (-2.7, -1.0, 0.0, 1.2, 2.8):
            for delta in (-2.9, -1.3, -0.2, 0.4, 2.7):
                forward, reverse = validate_edge_reversal(phi_i, phi_i + delta, coupling)
                assert forward.mobility_M == pytest.approx(reverse.mobility_M, abs=2e-12)
                assert forward.beta == pytest.approx(-reverse.beta, abs=2e-12)
                assert forward.activity == pytest.approx(reverse.activity, abs=2e-12)
                assert forward.current == pytest.approx(-reverse.current, abs=2e-12)
                assert forward.forward_rate > 0.0
                assert forward.reverse_rate > 0.0
                cases += 1
    assert cases == 100


def test_coupling_sign_is_preserved_as_parity_plus_oriented_drive():
    positive = edge_kinetics_from_qhtri(0.2, 1.1, 0.4)
    negative = edge_kinetics_from_qhtri(0.2, 1.1, -0.4)
    assert positive.coupling_magnitude == negative.coupling_magnitude
    assert positive.coupling_parity == 1
    assert negative.coupling_parity == -1
    assert positive.edge_drive == pytest.approx(-negative.edge_drive, abs=2e-12)
    assert positive.beta == pytest.approx(-negative.beta, abs=2e-12)


def test_principal_branch_cut_fails_closed():
    with pytest.raises(QhtriIdtEdgeKineticsError, match="branch cut"):
        edge_kinetics_from_qhtri(0.0, math.pi, 0.5)


def test_zero_coupling_fails_closed_for_positive_kinetic_realization():
    with pytest.raises(QhtriIdtEdgeKineticsError, match="non-zero coupling"):
        edge_kinetics_from_qhtri(0.1, 0.2, 0.0)


def test_receipt_roundtrip_and_tamper_detection():
    edge = edge_kinetics_from_qhtri(0.2, 1.1, -0.4)
    receipt = build_edge_kinetics_receipt(
        qhtri_tick=42,
        oscillator_i=2,
        oscillator_j=7,
        phi_lane_commitment="11" * 32,
        coupling_matrix_commitment="22" * 32,
        edge=edge,
    )
    validate_edge_kinetics_receipt(receipt)
    assert receipt["source_class"] == "NATURAL_SYSTEM_STATE"
    assert receipt["dynamics_class"] == "ENDOGENOUS_RUNTIME_DYNAMICS"
    assert receipt["evidence_status"] == "GREMLIN_STRUCTURAL_CANDIDATE"

    tampered = copy.deepcopy(receipt)
    tampered["kinetics"]["beta"] += 1e-3
    with pytest.raises(QhtriIdtEdgeKineticsError):
        validate_edge_kinetics_receipt(tampered)
