from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from tools.apocalypos_qhtri_closed_loop_v01 import (
    ClosedLoopError,
    build_postexecution_chain,
    build_preexecution_chain,
    build_semantic_bundle,
    validate_semantic_bundle,
)
from tools.vector_native_qhtri_replay_v01 import validate_source_snapshot

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "provenance"


def _load(name: str):
    return json.loads((PROVENANCE / name).read_text(encoding="utf-8"))


def _canonical_bytes(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _seal(body, key="receipt_sha256"):
    out = dict(body)
    out[key] = hashlib.sha256(_canonical_bytes(body)).hexdigest()
    return out


def _inputs():
    source = _load("BIOOS_VECTOR_NATIVE_QHTRI_SOURCE_V0_1.json")
    replay = _load("BIOOS_VECTOR_NATIVE_QHTRI_REPLAY_V0_1.json")
    bank = _load("GREMLIN_NOEMA_QHTRI_BANK_PIN_V0_1.json")
    state = validate_source_snapshot(source)
    build_body = {
        "schema": "BIOOS_VECTOR_NATIVE_QHTRI_QEMU_BUILD_V0_1",
        "status": "PASS_HOST_BUILD",
        "scope": "QEMU_TCG_VECTOR_NATIVE_QHTRI_EXACT_REPLAY_ROM",
        "source_receipt_sha256": state["source_receipt_sha256"],
        "working_state_sha256": state["working_state_sha256"],
        "source_tick": state["tick"],
        "replay_receipt_sha256": replay["replay_receipt_sha256"],
        "replay_binary_sha256": replay["replay_binary_sha256"],
        "rom_sha256": "a1" * 32,
        "qemu_executed": False,
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "physical_h200_execution_claim": False,
        "physical_qpu_claim": False,
        "physical_machine_claim": False,
        "epistemic": "CHYBA",
    }
    build = _seal(build_body)
    return source, replay, bank, build


def _conformance(source, replay, build):
    state = validate_source_snapshot(source)
    body = {
        "schema": "BIOOS_VECTOR_NATIVE_QHTRI_QEMU_CONFORMANCE_V0_1",
        "scope": "QEMU_TCG_VECTOR_NATIVE_QHTRI_EXACT_REPLAY_ROM",
        "status": "PASS_QEMU_VECTOR_NATIVE_REPLAY",
        "reason": None,
        "qemu_executed": True,
        "expected_sequence_present": True,
        "failure_marker_present": False,
        "source_receipt_sha256": state["source_receipt_sha256"],
        "working_state_sha256": state["working_state_sha256"],
        "source_tick": state["tick"],
        "replay_binary_sha256": replay["replay_binary_sha256"],
        "build_receipt_sha256": build["receipt_sha256"],
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "physical_h200_execution_claim": False,
        "physical_qpu_claim": False,
        "physical_machine_claim": False,
        "epistemic": "CHYBA",
    }
    return _seal(body)


def test_real_source_builds_full_semantic_bundle_without_execution_authority():
    source, replay, bank, _ = _inputs()
    bundle = build_semantic_bundle(source, replay, bank)
    validate_semantic_bundle(bundle, source, replay, bank)
    assert bundle["source_tick"] == source["tick"] == 20215
    assert bundle["semantic_loop"]["full_bank"] is True
    assert len(bundle["semantic_loop"]["ordered_isomorphism_ids"]) == 10
    assert bundle["candidate_only"] is True
    assert bundle["runtime_execution_authority"] is False
    assert bundle["canon_write_authority"] is False


def test_preexecution_admission_is_generation_bound_and_shadow_only():
    source, replay, bank, build = _inputs()
    bundle, grant, admission = build_preexecution_chain(source, replay, bank, build)
    assert admission["semantic_loop_receipt_sha256"] == bundle["semantic_loop"]["loop_receipt_sha256"]
    assert admission["pncap_grant_sha256"] == grant["grant_sha256"]
    assert admission["principal_generation_id"] == source["working_state_sha256"]
    assert admission["principal_generation_id"] == admission["environment_generation_id"]
    assert admission["shadow_execution_admitted"] is True
    assert admission["production_execution_admitted"] is False
    assert admission["physical_effect_authority"] is False


def test_closed_chain_binds_measured_qemu_receipt_and_emits_candidate_only_next_state():
    source, replay, bank, build = _inputs()
    bundle, grant, admission = build_preexecution_chain(source, replay, bank, build)
    conformance = _conformance(source, replay, build)
    result, reintegration, next_candidate, manifest = build_postexecution_chain(
        source, replay, bank, build, bundle, grant, admission, conformance
    )
    assert result["qemu_conformance_receipt_sha256"] == conformance["receipt_sha256"]
    assert reintegration["observed_state_commitment"] == conformance["receipt_sha256"]
    assert next_candidate["execution_observation_commitment"] == conformance["receipt_sha256"]
    assert next_candidate["transition_semantics"] == "PROVENANCE_ONLY_NO_DYNAMICAL_UPDATE_CLAIM"
    assert next_candidate["runtime_write"] is False
    assert manifest["status"] == "PASS_CLOSED_VECTOR_NATIVE_SHADOW_LOOP"
    assert manifest["shadow_execution_only"] is True
    assert manifest["physical_machine_claim"] is False
    assert manifest["physical_qpu_claim"] is False
    assert manifest["physical_h200_execution_claim"] is False


def test_bank_pin_mutation_fails_closed():
    source, replay, bank, _ = _inputs()
    tampered = copy.deepcopy(bank)
    tampered["bank_head_commit"] = "0" * 40
    bundle = build_semantic_bundle(source, replay, bank)
    with pytest.raises(ClosedLoopError, match="bank pin mismatch"):
        validate_semantic_bundle(bundle, source, replay, tampered)


def test_build_lineage_substitution_fails_before_admission():
    source, replay, bank, build = _inputs()
    tampered_body = {k: v for k, v in build.items() if k != "receipt_sha256"}
    tampered_body["source_tick"] = source["tick"] + 1
    tampered = _seal(tampered_body)
    with pytest.raises(ClosedLoopError, match="pre-execution admission failed"):
        build_preexecution_chain(source, replay, bank, tampered)


def test_qemu_result_substitution_fails_before_reintegration():
    source, replay, bank, build = _inputs()
    bundle, grant, admission = build_preexecution_chain(source, replay, bank, build)
    conformance = _conformance(source, replay, build)
    tampered_body = {k: v for k, v in conformance.items() if k != "receipt_sha256"}
    tampered_body["source_receipt_sha256"] = "ff" * 32
    tampered = _seal(tampered_body)
    with pytest.raises(ClosedLoopError, match="post-execution reintegration failed"):
        build_postexecution_chain(source, replay, bank, build, bundle, grant, admission, tampered)
