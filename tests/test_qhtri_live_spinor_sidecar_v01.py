from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from tools.noema_qhtri_live_bifurcation_ring_v01 import (
    LiveBifurcationRing,
    RingOrderingError,
)
from tools.noema_qhtri_semantic_loop_v01 import build_bifurcation_receipt
from tools.qhtri_live_spinor_sidecar_v01 import (
    EPOCH_SCHEMA,
    STEP_EVIDENCE_SCHEMA,
    LiveSpinorSidecarError,
    build_same_tick_spinor_receipt,
    publish_same_tick_bifurcation,
    read_same_tick_sidecar,
)
from tools.qhtri_spinor_lift_v01 import validate_spinor_lift_receipt


def _canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _sha(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _phase_sha(phi):
    arr = np.mod(np.asarray(phi, dtype="<f8").reshape(36), 2.0 * np.pi)
    return hashlib.sha256(arr.tobytes()).hexdigest()


def _turn_sha(turns):
    arr = np.asarray(turns, dtype="<i8").reshape(36)
    return hashlib.sha256(arr.tobytes()).hexdigest()


def _write_sidecar(root: Path, *, tick: int = 10, phi=None, turns=None):
    root.mkdir(parents=True, exist_ok=True)
    phi = np.asarray(
        np.linspace(0.0, 2.0 * np.pi, 36, endpoint=False) if phi is None else phi,
        dtype=np.float64,
    )
    turns = np.asarray(np.arange(36) % 5 if turns is None else turns, dtype=np.int64)
    epoch_body = {
        "schema": EPOCH_SCHEMA,
        "activation_tick": tick - 1,
        "activation_phase_sha256": _phase_sha(phi),
        "activation_ref": "TEST_ACTIVATION",
        "turns_dtype": "<i8",
        "turns_count": 36,
        "tick_dtype": "<u8",
    }
    epoch = {**epoch_body, "epoch_sha256": _sha(epoch_body)}
    operations = [
        {
            "kind": "KURAMOTO_PHASE_STEP",
            "increment_sha256": hashlib.sha256(np.ones(36, dtype="<f8").tobytes()).hexdigest(),
        }
    ]
    generator = _sha(
        {"qhtri_tick": tick, "epoch_sha256": epoch["epoch_sha256"], "operations": operations}
    )
    evidence_body = {
        "schema": STEP_EVIDENCE_SCHEMA,
        "qhtri_tick": tick,
        "epoch_sha256": epoch["epoch_sha256"],
        "projective_state_sha256": _phase_sha(phi),
        "turns_sha256": _turn_sha(turns),
        "generator_commitment": generator,
        "generator_operations": operations,
        "residual": [0.0] * 36,
        "uniqueness_margin": [float(np.pi)] * 36,
    }
    evidence = {**evidence_body, "step_evidence_sha256": _sha(evidence_body)}
    (root / "spinor_turns.i64").write_bytes(np.asarray(turns, dtype="<i8").tobytes())
    (root / "spinor_tick.u64").write_bytes(np.asarray([tick], dtype="<u8").tobytes())
    (root / "spinor_lift_epoch.json").write_bytes(_canonical(epoch))
    (root / "spinor_step_evidence.json").write_bytes(_canonical(evidence))
    return phi, turns, epoch, evidence


def _bifurcation(tick: int):
    h = hashlib.sha256
    return build_bifurcation_receipt(
        bank_manifest_sha256=h(b"bank").hexdigest(),
        qhtri_tick=tick,
        qhtri_state_commitment=h(b"state").hexdigest(),
        magnitude_M=0.75,
        beta=-0.1,
        generator_ref="test:qhtRI-edge",
        t36_witness_commitment=h(b"t36").hexdigest(),
        cp1_state_commitment=h(b"cp1").hexdigest(),
        telemetry_evidence_ref="test://telemetry",
    )


def test_same_tick_sidecar_builds_existing_spinor_receipt(tmp_path):
    phi, turns, _, evidence = _write_sidecar(tmp_path, tick=10)
    receipt = build_same_tick_spinor_receipt(
        sidecar_root=tmp_path,
        qhtri_tick=10,
        projected_phase=phi,
        source_evidence_ref="test://same-tick",
    )
    validate_spinor_lift_receipt(receipt)
    assert receipt["qhtri_tick"] == 10
    assert receipt["turns"] == [int(x) for x in turns]
    assert receipt["generator_commitment"] == evidence["generator_commitment"]


def test_tick_mismatch_fails_closed(tmp_path):
    phi, *_ = _write_sidecar(tmp_path, tick=10)
    with pytest.raises(LiveSpinorSidecarError, match="same-tick"):
        build_same_tick_spinor_receipt(
            sidecar_root=tmp_path,
            qhtri_tick=11,
            projected_phase=phi,
            source_evidence_ref="test://tick-mismatch",
        )


def test_projective_state_mismatch_fails_closed(tmp_path):
    phi, *_ = _write_sidecar(tmp_path, tick=10)
    phi = phi.copy()
    phi[0] += 0.2
    with pytest.raises(LiveSpinorSidecarError, match="projective-state"):
        read_same_tick_sidecar(sidecar_root=tmp_path, qhtri_tick=10, projected_phase=phi)


def test_resealed_turns_commitment_tamper_fails_closed(tmp_path):
    phi, *_ = _write_sidecar(tmp_path, tick=10)
    path = tmp_path / "spinor_step_evidence.json"
    value = json.loads(path.read_text())
    value["turns_sha256"] = "0" * 64
    body = {k: v for k, v in value.items() if k != "step_evidence_sha256"}
    value["step_evidence_sha256"] = _sha(body)
    path.write_bytes(_canonical(value))
    with pytest.raises(LiveSpinorSidecarError, match="turns mismatch"):
        read_same_tick_sidecar(sidecar_root=tmp_path, qhtri_tick=10, projected_phase=phi)


def test_resealed_generator_tamper_fails_closed(tmp_path):
    phi, *_ = _write_sidecar(tmp_path, tick=10)
    path = tmp_path / "spinor_step_evidence.json"
    value = json.loads(path.read_text())
    value["generator_operations"][0]["kind"] = "FORGED_KIND"
    body = {k: v for k, v in value.items() if k != "step_evidence_sha256"}
    value["step_evidence_sha256"] = _sha(body)
    path.write_bytes(_canonical(value))
    with pytest.raises(LiveSpinorSidecarError, match="generator commitment"):
        read_same_tick_sidecar(sidecar_root=tmp_path, qhtri_tick=10, projected_phase=phi)


def test_ring_event_promotes_spinor_status_to_present(tmp_path):
    sidecar = tmp_path / "sidecar"
    phi, *_ = _write_sidecar(sidecar, tick=10)
    ring = LiveBifurcationRing.create(tmp_path / "ring", capacity=4, slot_bytes=32768)
    record = publish_same_tick_bifurcation(
        ring,
        bifurcation_receipt=_bifurcation(10),
        sidecar_root=sidecar,
        projected_phase=phi,
        source_evidence_ref="test://ring-present",
    )
    assert record.event["spinor_status"] == "PRESENT"
    assert record.event["autonomy_level"] == "L0_OBSERVE_INTERPRET"
    assert record.event["runtime_effect_admitted"] is False
    read = ring.read_next()
    assert read is not None
    assert read.record_sha256 == record.record_sha256
    ring.ack(read.sequence, expected_record_sha256=read.record_sha256)


def test_ring_rejects_bifurcation_spinor_tick_mismatch(tmp_path):
    sidecar = tmp_path / "sidecar"
    phi, *_ = _write_sidecar(sidecar, tick=10)
    ring = LiveBifurcationRing.create(tmp_path / "ring", capacity=4, slot_bytes=32768)
    with pytest.raises(LiveSpinorSidecarError, match="same-tick"):
        publish_same_tick_bifurcation(
            ring,
            bifurcation_receipt=_bifurcation(11),
            sidecar_root=sidecar,
            projected_phase=phi,
            source_evidence_ref="test://ring-tick-mismatch",
        )
    assert ring.status()["head_sequence"] == 0


def test_partial_sidecar_fails_closed(tmp_path):
    phi, *_ = _write_sidecar(tmp_path, tick=10)
    (tmp_path / "spinor_step_evidence.json").unlink()
    with pytest.raises(LiveSpinorSidecarError, match="missing sidecar"):
        read_same_tick_sidecar(sidecar_root=tmp_path, qhtri_tick=10, projected_phase=phi)


def test_nonpositive_uniqueness_margin_fails_closed(tmp_path):
    phi, *_ = _write_sidecar(tmp_path, tick=10)
    path = tmp_path / "spinor_step_evidence.json"
    value = json.loads(path.read_text())
    value["uniqueness_margin"][7] = 0.0
    body = {k: v for k, v in value.items() if k != "step_evidence_sha256"}
    value["step_evidence_sha256"] = _sha(body)
    path.write_bytes(_canonical(value))
    with pytest.raises(LiveSpinorSidecarError, match="uniqueness margin"):
        read_same_tick_sidecar(sidecar_root=tmp_path, qhtri_tick=10, projected_phase=phi)
