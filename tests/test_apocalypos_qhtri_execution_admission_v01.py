from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from tools.apocalypos_qhtri_execution_admission_v01 import (
    ApocalypOSExecutionAdmissionError,
    BUILD_SCHEMA,
    BUILD_SCOPE,
    QEMU_CONFORMANCE_SCHEMA,
    QEMU_PASS_STATUS,
    build_execution_result,
    build_noema_reintegration_candidate,
    build_shadow_admission,
    build_shadow_grant,
    validate_noema_reintegration_candidate,
    validate_shadow_admission,
    validate_shadow_grant,
)
from tools.noema_qhtri_semantic_loop_v01 import (
    FULL_BANK_ISOMORPHISM_IDS,
    build_bifurcation_receipt,
    build_feedback_candidate_receipt,
    build_loop_receipt,
    build_projective_anchor_receipt,
    build_semantic_path_receipt,
    build_state_crystal_receipt,
)
from tools.vector_native_qhtri_replay_v01 import build_replay_receipt

SOURCE_PATH = Path("provenance/BIOOS_VECTOR_NATIVE_QHTRI_SOURCE_V0_1.json")
H = {
    "bank": "11" * 32,
    "qhtri": "12" * 32,
    "t36": "13" * 32,
    "cp1": "14" * 32,
    "adapter": "15" * 32,
    "holonomy": "16" * 32,
    "checkpoint": "17" * 32,
    "operator": "18" * 32,
    "rom": "19" * 32,
    "observed": "1a" * 32,
}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _seal(body, key="receipt_sha256"):
    out = dict(body)
    out[key] = hashlib.sha256(_canonical(body)).hexdigest()
    return out


def _semantic_fixture():
    bif = build_bifurcation_receipt(
        bank_manifest_sha256=H["bank"],
        qhtri_tick=20215,
        qhtri_state_commitment=H["qhtri"],
        magnitude_M=1.0,
        beta=0.125,
        generator_ref="QHTRI.GENERATOR.TEST",
        t36_witness_commitment=H["t36"],
        cp1_state_commitment=H["cp1"],
        telemetry_evidence_ref="QHTRI.SNAPSHOT.TEST",
    )
    anchor = build_projective_anchor_receipt(
        bif,
        poincare_re=0.15,
        poincare_im=-0.20,
        spinor_sheet=-1,
        cp1_poincare_adapter_commitment=H["adapter"],
        holonomy_audit_commitment=H["holonomy"],
    )
    semantic = build_semantic_path_receipt(
        (anchor,),
        ordered_relation_ids=(),
        ordered_kaku_candidate_ids=("KAKU.CAND.APOC.TEST",),
        ordered_radical_candidate_ids=("RADICAL.CAND.APOC.TEST",),
        ordered_operator_candidate_ids=("OP.CAND.APOC.TEST",),
        gremlin_isomorphism_ids=FULL_BANK_ISOMORPHISM_IDS,
    )
    crystal = build_state_crystal_receipt(
        semantic,
        state_object_id="STATE.APOC.TEST",
        pnfs_object_id="PNFS.APOC.TEST",
        generation=7,
        memory_epoch=7,
        checkpoint_commitment=H["checkpoint"],
    )
    feedback = build_feedback_candidate_receipt(
        crystal,
        hermitian_operator_commitment=H["operator"],
        pncap_admission_token="PNCAP.CANDIDATE.NOT_A_GRANT",
        qhtri_target_ref="QHTRI.BOUNDARY.NEXT",
    )
    loop = build_loop_receipt(
        bifurcation_receipt=bif,
        anchor_receipt=anchor,
        semantic_path_receipt=semantic,
        state_crystal_receipt=crystal,
        feedback_receipt=feedback,
    )
    return loop, feedback


def _source_and_replay():
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    return source, build_replay_receipt(source)


def _build_fixture(source, replay):
    body = {
        "schema": BUILD_SCHEMA,
        "status": "PASS_HOST_BUILD",
        "scope": BUILD_SCOPE,
        "source_receipt_sha256": source["receipt_sha256"],
        "working_state_sha256": source["working_state_sha256"],
        "source_tick": source["tick"],
        "replay_receipt_sha256": replay["replay_receipt_sha256"],
        "replay_binary_sha256": replay["replay_binary_sha256"],
        "rom_sha256": H["rom"],
        "qemu_executed": False,
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "physical_h200_execution_claim": False,
        "physical_qpu_claim": False,
        "physical_machine_claim": False,
    }
    return _seal(body)


def _conformance_fixture(source, replay, build):
    body = {
        "schema": QEMU_CONFORMANCE_SCHEMA,
        "scope": BUILD_SCOPE,
        "status": QEMU_PASS_STATUS,
        "reason": None,
        "source_tick": source["tick"],
        "source_receipt_sha256": source["receipt_sha256"],
        "working_state_sha256": source["working_state_sha256"],
        "replay_binary_sha256": replay["replay_binary_sha256"],
        "build_receipt_sha256": build["receipt_sha256"],
        "qemu_executed": True,
        "expected_sequence_present": True,
        "failure_marker_present": False,
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "physical_h200_execution_claim": False,
        "physical_qpu_claim": False,
        "physical_machine_claim": False,
    }
    return _seal(body)


def _full_fixture():
    loop, feedback = _semantic_fixture()
    source, replay = _source_and_replay()
    build = _build_fixture(source, replay)
    grant = build_shadow_grant(
        principal_generation_id="GEN.0007",
        environment_generation_id="GEN.0007",
        grant_id="PNCAP.SHADOW.GEN7.QEMU",
    )
    admission = build_shadow_admission(
        semantic_loop_receipt=loop,
        feedback_receipt=feedback,
        source_snapshot=source,
        replay_receipt=replay,
        qemu_build_receipt=build,
        pncap_shadow_grant=grant,
    )
    conformance = _conformance_fixture(source, replay, build)
    result = build_execution_result(admission, conformance)
    return loop, feedback, source, replay, build, grant, admission, conformance, result


def test_shadow_admission_and_reintegration_are_bounded():
    *_, admission, _, result = _full_fixture()
    validate_shadow_admission(admission)
    assert admission["shadow_execution_admitted"] is True
    assert admission["production_execution_admitted"] is False
    assert admission["physical_effect_authority"] is False
    assert result["execution_observed"] is True
    reintegration = build_noema_reintegration_candidate(
        result,
        observed_state_commitment=H["observed"],
        qhtri_next_target_ref="QHTRI.NEXT.CANDIDATE.TEST",
    )
    validate_noema_reintegration_candidate(reintegration)
    assert reintegration["candidate_only"] is True
    assert reintegration["runtime_execution_authority"] is False
    assert reintegration["canon_write_authority"] is False


def test_cross_generation_shadow_grant_fails_closed():
    with pytest.raises(ApocalypOSExecutionAdmissionError, match="generation mismatch"):
        build_shadow_grant(
            principal_generation_id="GEN.0007",
            environment_generation_id="GEN.0008",
            grant_id="PNCAP.CROSS.GEN",
        )


def test_wrong_capability_cannot_be_promoted_to_execution():
    with pytest.raises(ApocalypOSExecutionAdmissionError, match="capability mismatch"):
        build_shadow_grant(
            principal_generation_id="GEN.0007",
            environment_generation_id="GEN.0007",
            grant_id="PNCAP.WRONG.CAP",
            capability="BIND_DEVICE",
        )


def test_tampered_grant_seal_fails_closed():
    grant = build_shadow_grant(
        principal_generation_id="GEN.0007",
        environment_generation_id="GEN.0007",
        grant_id="PNCAP.TAMPER.TEST",
    )
    tampered = copy.deepcopy(grant)
    tampered["target_ref"] = "OTHER_TARGET"
    with pytest.raises(ApocalypOSExecutionAdmissionError, match="seal mismatch"):
        validate_shadow_grant(tampered)


def test_feedback_execution_escalation_is_rejected_before_admission():
    loop, feedback, source, replay, build, grant, *_ = _full_fixture()
    escalated = copy.deepcopy(feedback)
    body = {key: value for key, value in escalated.items() if key != "feedback_receipt_sha256"}
    body["execution_admitted"] = True
    escalated = _seal(body, "feedback_receipt_sha256")
    with pytest.raises(ApocalypOSExecutionAdmissionError, match="feedback candidate invalid"):
        build_shadow_admission(
            semantic_loop_receipt=loop,
            feedback_receipt=escalated,
            source_snapshot=source,
            replay_receipt=replay,
            qemu_build_receipt=build,
            pncap_shadow_grant=grant,
        )


def test_build_source_lineage_substitution_fails_closed():
    loop, feedback, source, replay, build, grant, *_ = _full_fixture()
    body = {key: value for key, value in build.items() if key != "receipt_sha256"}
    body["source_receipt_sha256"] = "ff" * 32
    substituted = _seal(body)
    with pytest.raises(ApocalypOSExecutionAdmissionError, match="build/source receipt lineage mismatch"):
        build_shadow_admission(
            semantic_loop_receipt=loop,
            feedback_receipt=feedback,
            source_snapshot=source,
            replay_receipt=replay,
            qemu_build_receipt=substituted,
            pncap_shadow_grant=grant,
        )


def test_failed_qemu_result_cannot_reenter_noema_as_success():
    *_, admission, conformance, _ = _full_fixture()
    body = {key: value for key, value in conformance.items() if key != "receipt_sha256"}
    body["status"] = "FAIL_QEMU_VECTOR_NATIVE_REPLAY"
    body["reason"] = "INJECTED_FAILURE"
    failed = _seal(body)
    with pytest.raises(ApocalypOSExecutionAdmissionError, match="did not pass"):
        build_execution_result(admission, failed)


def test_conformance_from_other_build_is_rejected():
    *_, admission, conformance, _ = _full_fixture()
    body = {key: value for key, value in conformance.items() if key != "receipt_sha256"}
    body["build_receipt_sha256"] = "ee" * 32
    substituted = _seal(body)
    with pytest.raises(ApocalypOSExecutionAdmissionError, match="conformance/build lineage mismatch"):
        build_execution_result(admission, substituted)
