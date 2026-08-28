from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import struct

import pytest

from tools.noema_qhtri_live_bifurcation_ring_v01 import (
    AUTONOMY_LEVEL,
    FOOTER,
    HEADER,
    LiveBifurcationRing,
    RingCorruptionError,
    RingFullError,
    RingOrderingError,
    build_transport_event,
    validate_transport_event,
)


def cbytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def seal(body, key):
    return {**body, key: hashlib.sha256(cbytes(body)).hexdigest()}


def h(label):
    return hashlib.sha256(label.encode()).hexdigest()


def bif(tick: int):
    return seal(
        {
            "schema": "BIOOS-NOEMA-QHTRI-BIFURCATION/0.1",
            "bank_manifest_sha256": h("bank"),
            "qhtri_tick": tick,
            "qhtri_state_commitment": h(f"state:{tick}"),
            "magnitude_M": 0.5,
            "beta": 0.01 * tick,
            "generator_ref": "test:edge:0:1",
            "t36_witness_commitment": h(f"t36:{tick}"),
            "cp1_state_commitment": h(f"cp1:{tick}"),
            "telemetry_evidence_ref": f"test:telemetry:{tick}",
            "source_class": "NATURAL_SYSTEM_STATE",
            "dynamics_class": "ENDOGENOUS_RUNTIME_DYNAMICS",
        },
        "bifurcation_receipt_sha256",
    )


def spinor(tick: int):
    body = {
        "schema": "BIOOS-QHTRI-SPINOR-LIFT/0.1",
        "tracker_id": "QHTRI.SPINOR.LIFT.NEAREST_GENERATOR_V0_1",
        "isomorphism_id": "ISO.NQ.04.SPINOR.SHEET.WITNESS",
        "qhtri_tick": tick,
        "projective_state_commitment": h(f"projective:{tick}"),
        "generator_commitment": h(f"generator:{tick}"),
        "projected_phase": [0.1, 0.2, 0.3],
        "turns": [tick % 2, 0, 2],
        "spinor_sheet": [-1 if tick % 2 else 1, 1, 1],
        "residual": [0.0, 0.0, 0.0],
        "uniqueness_margin": [3.0, 3.0, 3.0],
        "source_evidence_ref": f"test:spinor:{tick}",
        "source_class": "NATURAL_SYSTEM_STATE",
        "dynamics_class": "ENDOGENOUS_RUNTIME_DYNAMICS",
        "evidence_status": "GREMLIN_STRUCTURAL_CANDIDATE",
    }
    return seal(body, "spinor_lift_receipt_sha256")


def ring(tmp_path: Path, capacity=4, slot_bytes=8192):
    return LiveBifurcationRing.create(
        tmp_path / "ring",
        capacity=capacity,
        slot_bytes=slot_bytes,
        ring_epoch="test-epoch",
    )


def test_create_open_empty_ring(tmp_path):
    r = ring(tmp_path)
    assert r.status()["pending_count"] == 0
    assert r.status()["autonomy_level"] == AUTONOMY_LEVEL
    assert r.status()["human_per_tick_authorization_required"] is False
    assert r.read_next() is None
    reopened = LiveBifurcationRing.open(r.root)
    assert reopened.status() == r.status()


def test_publish_read_ack_pending_spinor(tmp_path):
    r = ring(tmp_path)
    pub = r.publish(qhtri_tick=10, bifurcation_receipt=bif(10))
    assert pub.sequence == 1
    rec = r.read_next()
    assert rec is not None
    assert rec.record_sha256 == pub.record_sha256
    assert rec.event["spinor_status"] == "PENDING"
    assert rec.event["runtime_write_scope"] == "TRANSPORT_ONLY"
    cursor = r.ack(1, expected_record_sha256=rec.record_sha256)
    assert cursor["ack_sequence"] == 1
    assert r.read_next() is None
    assert r.verify_pending_chain()["status"] == "PASS"


def test_publish_present_spinor_same_tick(tmp_path):
    r = ring(tmp_path)
    pub = r.publish(qhtri_tick=7, bifurcation_receipt=bif(7), spinor_lift_receipt=spinor(7))
    assert pub.event["spinor_status"] == "PRESENT"
    assert pub.event["spinor_lift_receipt_sha256"] == spinor(7)["spinor_lift_receipt_sha256"]
    assert r.read_next().event["spinor_status"] == "PRESENT"


def test_spinor_tick_mismatch_fails_closed(tmp_path):
    r = ring(tmp_path)
    with pytest.raises(RingOrderingError):
        r.publish(qhtri_tick=7, bifurcation_receipt=bif(7), spinor_lift_receipt=spinor(8))
    assert r.status()["head_sequence"] == 0


def test_tick_must_be_strictly_increasing(tmp_path):
    r = ring(tmp_path)
    r.publish(qhtri_tick=10, bifurcation_receipt=bif(10))
    with pytest.raises(RingOrderingError):
        r.publish(qhtri_tick=10, bifurcation_receipt=bif(10))
    with pytest.raises(RingOrderingError):
        r.publish(qhtri_tick=9, bifurcation_receipt=bif(9))
    assert r.status()["head_sequence"] == 1


def test_overflow_never_overwrites_unread_and_wrap_after_ack(tmp_path):
    r = ring(tmp_path, capacity=2)
    first = r.publish(qhtri_tick=1, bifurcation_receipt=bif(1))
    second = r.publish(qhtri_tick=2, bifurcation_receipt=bif(2))
    with pytest.raises(RingFullError):
        r.publish(qhtri_tick=3, bifurcation_receipt=bif(3))
    assert r.read_next().record_sha256 == first.record_sha256
    r.ack(1, expected_record_sha256=first.record_sha256)
    third = r.publish(qhtri_tick=3, bifurcation_receipt=bif(3))
    assert third.sequence == 3
    nxt = r.read_next()
    assert nxt.sequence == 2
    assert nxt.record_sha256 == second.record_sha256
    r.ack(2, expected_record_sha256=second.record_sha256)
    nxt = r.read_next()
    assert nxt.sequence == 3
    assert nxt.record_sha256 == third.record_sha256
    r.ack(3, expected_record_sha256=third.record_sha256)
    assert r.status()["pending_count"] == 0


def test_ack_requires_exact_next_sequence(tmp_path):
    r = ring(tmp_path)
    r.publish(qhtri_tick=1, bifurcation_receipt=bif(1))
    r.publish(qhtri_tick=2, bifurcation_receipt=bif(2))
    with pytest.raises(RingOrderingError):
        r.ack(2)
    r.ack(1)
    with pytest.raises(RingOrderingError):
        r.ack(1)


def test_parent_hash_chain_survives_reopen(tmp_path):
    r = ring(tmp_path)
    pubs = [r.publish(qhtri_tick=t, bifurcation_receipt=bif(t)) for t in (10, 11, 12)]
    assert pubs[1].parent_record_sha256 == pubs[0].record_sha256
    assert pubs[2].parent_record_sha256 == pubs[1].record_sha256
    reopened = LiveBifurcationRing.open(r.root)
    report = reopened.verify_pending_chain()
    assert report["pending_count"] == 3
    for p in pubs:
        rec = reopened.read_next()
        assert rec.sequence == p.sequence
        reopened.ack(rec.sequence, expected_record_sha256=rec.record_sha256)


def test_payload_tamper_detected(tmp_path):
    r = ring(tmp_path)
    p = r.publish(qhtri_tick=1, bifurcation_receipt=bif(1))
    state = json.loads(r.state_path.read_text())
    offset = 0
    with r.ring_path.open("r+b", buffering=0) as f:
        f.seek(HEADER.size + 5)
        original = f.read(1)
        f.seek(HEADER.size + 5)
        f.write(bytes([original[0] ^ 1]))
        os.fsync(f.fileno())
    with pytest.raises(RingCorruptionError, match="payload hash"):
        r.read_next()


def test_torn_footer_detected(tmp_path):
    r = ring(tmp_path)
    r.publish(qhtri_tick=1, bifurcation_receipt=bif(1))
    state = json.loads(r.state_path.read_text())
    slot_bytes = state["slot_bytes"]
    with r.ring_path.open("r+b", buffering=0) as f:
        f.seek(slot_bytes - FOOTER.size)
        f.write(b"\x00\x00\x00\x00")
        os.fsync(f.fileno())
    with pytest.raises(RingCorruptionError, match="magic"):
        r.read_next()


def test_state_and_cursor_tamper_detected(tmp_path):
    r = ring(tmp_path)
    state = json.loads(r.state_path.read_text())
    state["head_sequence"] = 1
    r.state_path.write_text(json.dumps(state))
    with pytest.raises(RingCorruptionError, match="state_sha256"):
        r.status()

    r2 = LiveBifurcationRing.create(tmp_path / "ring2", capacity=2, slot_bytes=8192, ring_epoch="x")
    cursor = json.loads(r2.cursor_path.read_text())
    cursor["ack_sequence"] = 1
    r2.cursor_path.write_text(json.dumps(cursor))
    with pytest.raises(RingCorruptionError, match="cursor_sha256"):
        r2.status()


def test_l0_authority_escalation_rejected_even_with_recomputed_event_seal():
    event = build_transport_event(
        sequence=1,
        parent_record_sha256=h("parent"),
        qhtri_tick=5,
        bifurcation_receipt=bif(5),
    )
    body = {k: v for k, v in event.items() if k != "event_sha256"}
    body["external_effect"] = True
    tampered = seal(body, "event_sha256")
    with pytest.raises(RingCorruptionError, match="external_effect"):
        validate_transport_event(tampered)


def test_recomputed_bifurcation_seal_still_requires_declared_source_class(tmp_path):
    bad = bif(2)
    body = {k: v for k, v in bad.items() if k != "bifurcation_receipt_sha256"}
    body["source_class"] = "OTHER"
    bad = seal(body, "bifurcation_receipt_sha256")
    r = ring(tmp_path)
    with pytest.raises(Exception, match="source class"):
        r.publish(qhtri_tick=2, bifurcation_receipt=bad)


def test_record_hash_required_on_ack(tmp_path):
    r = ring(tmp_path)
    pub = r.publish(qhtri_tick=1, bifurcation_receipt=bif(1))
    with pytest.raises(RingCorruptionError, match="expected SHA"):
        r.ack(1, expected_record_sha256=h("wrong"))
    assert r.status()["ack_sequence"] == 0
    r.ack(1, expected_record_sha256=pub.record_sha256)


def test_bifurcation_negative_magnitude_rejected_even_with_valid_seal(tmp_path):
    r = ring(tmp_path)
    receipt = bif(1)
    body = {k: v for k, v in receipt.items() if k != "bifurcation_receipt_sha256"}
    body["magnitude_M"] = -0.001
    bad = seal(body, "bifurcation_receipt_sha256")
    with pytest.raises(Exception, match="magnitude_M"):
        r.publish(qhtri_tick=1, bifurcation_receipt=bad)
    assert r.status()["head_sequence"] == 0


def test_bifurcation_non_numeric_beta_rejected_even_with_valid_seal(tmp_path):
    r = ring(tmp_path)
    receipt = bif(1)
    body = {k: v for k, v in receipt.items() if k != "bifurcation_receipt_sha256"}
    body["beta"] = "bad-beta"
    bad = seal(body, "bifurcation_receipt_sha256")
    with pytest.raises(Exception, match="magnitude_M and beta must be numeric"):
        r.publish(qhtri_tick=1, bifurcation_receipt=bad)
    assert r.status()["head_sequence"] == 0
