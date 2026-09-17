from __future__ import annotations

import hashlib
import json
import struct

import pytest

from tools.pnvector_handoff_builder_v01 import build as build_pnvh
from tools.qemu_qhtri_vector_replay_build_v01 import BASIS_BINDING, load_source
from tools.qemu_qhtri_vector_replay_conformance_v01 import verify_pnvh_against_source

SOURCE = "provenance/BIOOS_VECTOR_NATIVE_QHTRI_SOURCE_V0_1.json"


def _source_obj():
    raw = open(SOURCE, "rb").read()
    return raw, json.loads(raw.decode("utf-8"))


def test_frozen_same_tick_qhtri_source_is_admissible():
    obj, raw, phi, omega = load_source(__import__("pathlib").Path(SOURCE))
    assert obj["tick"] == obj["surface_state"]["noema_tick"]
    assert len(phi) == 36
    assert len(omega) == 36
    assert hashlib.sha256(struct.pack("<36d", *phi)).hexdigest() == obj["phi_raw_sha256"]
    assert hashlib.sha256(struct.pack("<36d", *omega)).hexdigest() == obj["omega_raw_sha256"]
    assert hashlib.sha256(raw).hexdigest()


def test_source_rejects_phi_tamper(tmp_path):
    _, obj = _source_obj()
    obj["phi"][0] = float(obj["phi"][0]) + 0.125
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(obj), encoding="utf-8")
    with pytest.raises(ValueError, match="phi_raw_sha256 mismatch"):
        load_source(path)


def test_source_rejects_cross_tick_surface_mix(tmp_path):
    _, obj = _source_obj()
    obj["surface_state"]["noema_tick"] = int(obj["tick"]) + 1
    path = tmp_path / "cross-tick.json"
    path.write_text(json.dumps(obj), encoding="utf-8")
    with pytest.raises(ValueError, match="same-tick"):
        load_source(path)


def test_source_rejects_physical_qpu_claim_escalation(tmp_path):
    _, obj = _source_obj()
    obj["physical_qpu_claim"] = True
    path = tmp_path / "claim-escalation.json"
    path.write_text(json.dumps(obj), encoding="utf-8")
    with pytest.raises(ValueError, match="physical QPU"):
        load_source(path)


def test_pnvh_contains_exact_qhtri_phi_and_source_context():
    raw, source = _source_obj()
    phi = tuple(float(v) for v in source["phi"])
    vector = struct.pack("<36d", *phi)
    pnvh = build_pnvh(
        vector,
        bytes.fromhex(BASIS_BINDING),
        hashlib.sha256(raw).digest(),
        0x7,
    )
    info = verify_pnvh_against_source(pnvh, source)
    assert info["vector_sha256"] == source["phi_raw_sha256"]
    assert info["source_context_sha256"] == hashlib.sha256(raw).hexdigest()


def test_pnvh_rejects_different_vector_even_if_self_consistent():
    raw, source = _source_obj()
    phi = [float(v) for v in source["phi"]]
    phi[0] += 0.25
    vector = struct.pack("<36d", *phi)
    pnvh = build_pnvh(
        vector,
        bytes.fromhex(BASIS_BINDING),
        hashlib.sha256(raw).digest(),
        0x7,
    )
    with pytest.raises(ValueError, match="do not exactly equal"):
        verify_pnvh_against_source(pnvh, source)
