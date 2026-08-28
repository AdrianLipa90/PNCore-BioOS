from __future__ import annotations

import hashlib
import json

import pytest

from tools.noema_qhtri_live_bifurcation_ring_v01 import LiveBifurcationRing, LiveBifurcationRingError


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def seal(body, key):
    return {**body, key: hashlib.sha256(canonical(body)).hexdigest()}


def bif(tick):
    body = {
        "schema": "BIOOS-NOEMA-QHTRI-BIFURCATION/0.1",
        "bank_manifest_sha256": "1" * 64,
        "qhtri_tick": tick,
        "qhtri_state_commitment": "2" * 64,
        "magnitude_M": 0.2,
        "beta": 0.1,
        "generator_ref": "test",
        "t36_witness_commitment": "3" * 64,
        "cp1_state_commitment": "4" * 64,
        "telemetry_evidence_ref": "shadow:test",
        "source_class": "NATURAL_SYSTEM_STATE",
        "dynamics_class": "ENDOGENOUS_RUNTIME_DYNAMICS",
    }
    return seal(body, "bifurcation_receipt_sha256")


def spin(tick, turns=(0, 1, -2, 3)):
    body = {
        "schema": "BIOOS-QHTRI-SPINOR-LIFT/0.1",
        "tracker_id": "QHTRI.SPINOR.LIFT.NEAREST_GENERATOR_V0_1",
        "isomorphism_id": "ISO.NQ.04.SPINOR.SHEET.WITNESS",
        "qhtri_tick": tick,
        "projective_state_commitment": "5" * 64,
        "generator_commitment": "6" * 64,
        "projected_phase": [0.1] * len(turns),
        "turns": list(turns),
        "spinor_sheet": [1 if x % 2 == 0 else -1 for x in turns],
        "residual": [0.0] * len(turns),
        "uniqueness_margin": [3.0] * len(turns),
        "source_evidence_ref": "shadow:test",
        "source_class": "NATURAL_SYSTEM_STATE",
        "dynamics_class": "ENDOGENOUS_RUNTIME_DYNAMICS",
        "evidence_status": "GREMLIN_STRUCTURAL_CANDIDATE",
    }
    return seal(body, "spinor_lift_receipt_sha256")


def make(tmp, capacity=3):
    return LiveBifurcationRing(tmp / "ring", capacity=capacity, producer_id="qhtri:gpu0", allow_shadow_path=True)


def test_order_ack_and_reopen(tmp_path):
    ring = make(tmp_path, 3)
    ring.register_consumer("noema")
    e0 = ring.append(bif(10), spinor_lift_receipt=spin(10))
    e1 = ring.append(bif(11), spinor_lift_receipt=spin(11))
    assert ring.read_next("noema")["event_sha256"] == e0["event_sha256"]
    ring.ack("noema", e0)
    assert ring.read_next("noema")["event_sha256"] == e1["event_sha256"]
    reopened = LiveBifurcationRing(tmp_path / "ring", producer_id="qhtri:gpu0", capacity=3, allow_shadow_path=True)
    reopened.ack("noema", e1)
    assert reopened.read_next("noema") is None
    assert reopened.audit_committed_window()["status"] == "PASS"


def test_fail_closed_overflow_then_ack_releases_slot(tmp_path):
    ring = make(tmp_path, 3)
    ring.register_consumer("noema")
    events = [ring.append(bif(t), spinor_lift_receipt=spin(t)) for t in (20, 21, 22)]
    with pytest.raises(LiveBifurcationRingError, match="RING_OVERFLOW_UNACKED"):
        ring.append(bif(23), spinor_lift_receipt=spin(23))
    ring.ack("noema", events[0])
    assert ring.append(bif(23), spinor_lift_receipt=spin(23))["sequence"] == 3
    assert ring.audit_committed_window()["retained_start_sequence"] == 1


def test_multiple_consumers_slowest_controls_overflow(tmp_path):
    ring = make(tmp_path, 2)
    ring.register_consumer("a")
    ring.register_consumer("b")
    e0 = ring.append(bif(30), spinor_lift_receipt=spin(30))
    e1 = ring.append(bif(31), spinor_lift_receipt=spin(31))
    ring.ack("a", e0)
    ring.ack("a", e1)
    with pytest.raises(LiveBifurcationRingError, match="RING_OVERFLOW_UNACKED"):
        ring.append(bif(32), spinor_lift_receipt=spin(32))
    ring.ack("b", e0)
    assert ring.append(bif(32), spinor_lift_receipt=spin(32))["sequence"] == 2


def test_wrong_producer_denied(tmp_path):
    ring = make(tmp_path)
    ring.register_consumer("n")
    with pytest.raises(LiveBifurcationRingError, match="producer ownership"):
        ring.append(bif(1), spinor_lift_receipt=spin(1), producer_id="other")


def test_tick_mismatch_denied(tmp_path):
    ring = make(tmp_path)
    with pytest.raises(LiveBifurcationRingError, match="tick mismatch"):
        ring.append(bif(1), spinor_lift_receipt=spin(2))


def test_spinor_required(tmp_path):
    ring = make(tmp_path)
    with pytest.raises(LiveBifurcationRingError, match="spinor lift receipt required"):
        ring.append(bif(1))


def test_tampered_event_even_resealed_is_denied_by_child_binding(tmp_path):
    ring = make(tmp_path)
    ring.register_consumer("n")
    ring.append(bif(40), spinor_lift_receipt=spin(40))
    path = ring._slot_path(0)
    value = json.loads(path.read_text())
    value["bifurcation_receipt"]["qhtri_tick"] = 41
    body = {k: v for k, v in value.items() if k != "event_sha256"}
    value["event_sha256"] = hashlib.sha256(canonical(body)).hexdigest()
    path.write_text(json.dumps(value))
    with pytest.raises(LiveBifurcationRingError):
        ring.read_next("n")


def test_torn_slot_denied(tmp_path):
    ring = make(tmp_path)
    ring.register_consumer("n")
    ring.append(bif(50), spinor_lift_receipt=spin(50))
    ring._slot_path(0).write_bytes(b'{"schema":')
    with pytest.raises(LiveBifurcationRingError, match="invalid/torn JSON"):
        ring.read_next("n")


def test_ack_out_of_order_denied(tmp_path):
    ring = make(tmp_path)
    ring.register_consumer("n")
    e0 = ring.append(bif(60), spinor_lift_receipt=spin(60))
    e1 = ring.append(bif(61), spinor_lift_receipt=spin(61))
    with pytest.raises(LiveBifurcationRingError, match="ACK_OUT_OF_ORDER"):
        ring.ack("n", e1)
    ring.ack("n", e0)


def test_audit_detects_nonmonotonic_qhtri_ticks(tmp_path):
    ring = make(tmp_path)
    ring.register_consumer("n")
    ring.append(bif(70), spinor_lift_receipt=spin(70))
    ring.append(bif(69), spinor_lift_receipt=spin(69))
    with pytest.raises(LiveBifurcationRingError, match="QHTRI_TICK_NOT_STRICTLY_INCREASING"):
        ring.audit_committed_window()


def test_operational_path_guard(tmp_path):
    with pytest.raises(LiveBifurcationRingError, match="/dev/shm/ciel_noema"):
        LiveBifurcationRing(tmp_path / "x", capacity=2, producer_id="p")


def test_transport_remains_l0(tmp_path):
    ring = make(tmp_path)
    ring.register_consumer("n")
    event = ring.append(bif(80), spinor_lift_receipt=spin(80))
    assert event["transport_authority"] == "L0_OBSERVE_INTERPRET"
    assert event["runtime_effect_admitted"] is False
