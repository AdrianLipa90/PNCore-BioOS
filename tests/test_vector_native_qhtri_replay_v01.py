import copy
import math

import pytest

from tools.vector_native_qhtri_replay_v01 import (
    VectorNativeReplayError,
    build_replay_binary,
    build_replay_receipt,
    decode_replay_binary,
    validate_replay_receipt,
    validate_source_snapshot,
)


def _source():
    phi = [0.1 + i * 0.01 for i in range(36)]
    omega = [39.0 + i * 0.02 for i in range(36)]
    return {
        "schema": "BIOOS_VECTOR_NATIVE_QHTRI_SOURCE_V0_1",
        "status": "LIVE_SAME_TICK_SNAPSHOT_CAPTURED_FOR_EMULATION_REPLAY",
        "source_class": "NATURAL_SYSTEM_STATE",
        "dynamics_class": "ENDOGENOUS_RUNTIME_DYNAMICS",
        "tether_status": "ACTIVE",
        "canon_allowed": False,
        "physical_h200_execution_claim": False,
        "physical_qpu_claim": False,
        "dimension": 36,
        "tick": 20215,
        "phi": phi,
        "omega": omega,
        "phi_raw_sha256": "11" * 32,
        "omega_raw_sha256": "22" * 32,
        "receipt_sha256": "33" * 32,
        "working_state_sha256": "44" * 32,
        "selected_edge": {
            "oscillator_i": 24,
            "oscillator_j": 26,
            "coupling": 1.0,
            "phi_i": phi[24],
            "phi_j": phi[26],
            "poincare_i": [-0.18, 0.06],
            "poincare_j": [0.18, 0.06],
        },
    }


def test_replay_binary_roundtrip_is_exact_and_deterministic():
    source = _source()
    first = build_replay_binary(source)
    second = build_replay_binary(source)
    assert first == second

    decoded = decode_replay_binary(first)
    assert decoded["dimension"] == 36
    assert decoded["tick"] == source["tick"]
    assert decoded["oscillator_i"] == 24
    assert decoded["oscillator_j"] == 26
    assert decoded["coupling"] == 1.0
    assert decoded["phi"] == tuple(source["phi"])
    assert decoded["omega"] == tuple(source["omega"])
    assert decoded["source_receipt_sha256"] == source["receipt_sha256"]
    assert decoded["working_state_sha256"] == source["working_state_sha256"]


def test_replay_receipt_is_non_authoritative_and_reconstructible():
    source = _source()
    receipt = build_replay_receipt(source)
    assert receipt["runtime_execution_authority"] is False
    assert receipt["canon_write_authority"] is False
    assert receipt["physical_h200_execution_claim"] is False
    assert receipt["physical_qpu_claim"] is False
    assert receipt["epistemic"] == "CHYBA"
    validate_replay_receipt(receipt, source)


def test_source_rejects_dimension_mismatch():
    source = _source()
    source["dimension"] = 35
    with pytest.raises(VectorNativeReplayError, match="dimension"):
        validate_source_snapshot(source)


def test_source_rejects_selected_edge_lane_mismatch():
    source = _source()
    source["selected_edge"]["phi_i"] += 0.25
    with pytest.raises(VectorNativeReplayError, match="phi_i"):
        validate_source_snapshot(source)


def test_source_rejects_nonfinite_lane():
    source = _source()
    source["omega"][7] = math.inf
    with pytest.raises(VectorNativeReplayError, match="finite"):
        validate_source_snapshot(source)


def test_source_rejects_missing_live_tether_witness():
    source = _source()
    source["tether_status"] = "STALE"
    with pytest.raises(VectorNativeReplayError, match="ACTIVE tether"):
        validate_source_snapshot(source)


def test_source_rejects_authority_escalation():
    source = _source()
    source["canon_allowed"] = True
    with pytest.raises(VectorNativeReplayError, match="canon authority"):
        validate_source_snapshot(source)


def test_replay_receipt_tamper_fails():
    source = _source()
    receipt = build_replay_receipt(source)
    tampered = copy.deepcopy(receipt)
    tampered["selected_edge"]["coupling"] = 0.5
    with pytest.raises(VectorNativeReplayError, match="deterministic reconstruction"):
        validate_replay_receipt(tampered, source)


def test_source_rejects_poincare_boundary():
    source = _source()
    source["selected_edge"]["poincare_i"] = [1.0, 0.0]
    with pytest.raises(VectorNativeReplayError, match="unit disk"):
        validate_source_snapshot(source)
