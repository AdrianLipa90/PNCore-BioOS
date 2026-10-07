from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from tools.noema_qhtri_semantic_loop_v01 import validate_feedback_candidate_receipt
from tools.vector_native_qhtri_replay_v01 import validate_replay_receipt, validate_source_snapshot

GRANT_SCHEMA = "APOCALYPOS_PNCAP_SHADOW_GRANT_V0_1"
ADMISSION_SCHEMA = "APOCALYPOS_QHTRI_EXECUTION_ADMISSION_V0_1"
RESULT_SCHEMA = "APOCALYPOS_QHTRI_EXECUTION_RESULT_V0_1"
REINTEGRATION_SCHEMA = "NOEMA_QHTRI_REINTEGRATION_CANDIDATE_V0_1"

LOOP_SCHEMA = "BIOOS-NOEMA-QHTRI-SEMANTIC-LOOP/0.1"
BUILD_SCHEMA = "BIOOS_VECTOR_NATIVE_QHTRI_QEMU_BUILD_V0_1"
BUILD_SCOPE = "QEMU_TCG_VECTOR_NATIVE_QHTRI_EXACT_REPLAY_ROM"
QEMU_CONFORMANCE_SCHEMA = "BIOOS_VECTOR_NATIVE_QHTRI_QEMU_CONFORMANCE_V0_1"
QEMU_PASS_STATUS = "PASS_QEMU_VECTOR_NATIVE_REPLAY"

CAPABILITY = "EXECUTE_PROGRAM"
TARGET_REF = "QEMU_QHTRI_VECTOR_REPLAY"
OPERATION_REF = "SHADOW_QEMU"
EPISTEMIC = "CHYBA"


class ApocalypOSExecutionAdmissionError(ValueError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _text(value: Any, name: str) -> str:
    if value is None:
        raise ApocalypOSExecutionAdmissionError(f"{name} is required")
    text = str(value).strip()
    if not text:
        raise ApocalypOSExecutionAdmissionError(f"{name} is required")
    return text


def _hex64(value: Any, name: str) -> str:
    text = _text(value, name).lower()
    if len(text) != 64:
        raise ApocalypOSExecutionAdmissionError(f"{name} must be 64 hex characters")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise ApocalypOSExecutionAdmissionError(f"{name} must be hexadecimal") from exc
    return text


def _seal(body: Mapping[str, Any], seal_key: str) -> dict[str, Any]:
    if seal_key in body:
        raise ApocalypOSExecutionAdmissionError(f"seal key already present: {seal_key}")
    out = dict(body)
    out[seal_key] = _sha256(body)
    return out


def _verify_seal(receipt: Mapping[str, Any], seal_key: str) -> None:
    recorded = _hex64(receipt.get(seal_key), seal_key)
    body = {key: value for key, value in receipt.items() if key != seal_key}
    if _sha256(body) != recorded:
        raise ApocalypOSExecutionAdmissionError(f"seal mismatch: {seal_key}")


def _must_be_false(receipt: Mapping[str, Any], key: str) -> None:
    if receipt.get(key) is not False:
        raise ApocalypOSExecutionAdmissionError(f"authority boundary open: {key}")


def _validate_semantic_loop_candidate(loop: Mapping[str, Any]) -> None:
    if loop.get("schema") != LOOP_SCHEMA:
        raise ApocalypOSExecutionAdmissionError("semantic loop schema mismatch")
    _verify_seal(loop, "loop_receipt_sha256")
    _hex64(loop.get("feedback_receipt_sha256"), "feedback_receipt_sha256")
    _hex64(loop.get("semantic_path_receipt_sha256"), "semantic_path_receipt_sha256")
    _hex64(loop.get("state_crystal_receipt_sha256"), "state_crystal_receipt_sha256")
    _must_be_false(loop, "runtime_execution_authority")
    _must_be_false(loop, "canon_write_authority")
    if loop.get("epistemic") != EPISTEMIC:
        raise ApocalypOSExecutionAdmissionError("semantic loop epistemic state mismatch")


def _validate_build_receipt(
    build: Mapping[str, Any],
    *,
    source_state: Mapping[str, Any],
    replay_receipt: Mapping[str, Any],
) -> None:
    if build.get("schema") != BUILD_SCHEMA:
        raise ApocalypOSExecutionAdmissionError("QEMU build schema mismatch")
    if build.get("status") != "PASS_HOST_BUILD" or build.get("scope") != BUILD_SCOPE:
        raise ApocalypOSExecutionAdmissionError("QEMU build did not pass the exact replay build gate")
    _verify_seal(build, "receipt_sha256")
    _must_be_false(build, "qemu_executed")
    for key in (
        "runtime_execution_authority",
        "canon_write_authority",
        "physical_h200_execution_claim",
        "physical_qpu_claim",
        "physical_machine_claim",
    ):
        _must_be_false(build, key)
    if build.get("source_receipt_sha256") != source_state["source_receipt_sha256"]:
        raise ApocalypOSExecutionAdmissionError("build/source receipt lineage mismatch")
    if build.get("working_state_sha256") != source_state["working_state_sha256"]:
        raise ApocalypOSExecutionAdmissionError("build/source working-state lineage mismatch")
    if build.get("source_tick") != source_state["tick"]:
        raise ApocalypOSExecutionAdmissionError("build/source tick lineage mismatch")
    if build.get("replay_receipt_sha256") != replay_receipt.get("replay_receipt_sha256"):
        raise ApocalypOSExecutionAdmissionError("build/replay receipt lineage mismatch")
    _hex64(build.get("replay_binary_sha256"), "replay_binary_sha256")
    _hex64(build.get("rom_sha256"), "rom_sha256")


def build_shadow_grant(
    *,
    principal_generation_id: str,
    environment_generation_id: str,
    grant_id: str,
    capability: str = CAPABILITY,
    target_ref: str = TARGET_REF,
    operation_ref: str = OPERATION_REF,
) -> dict[str, Any]:
    principal = _text(principal_generation_id, "principal_generation_id")
    environment = _text(environment_generation_id, "environment_generation_id")
    if principal != environment:
        raise ApocalypOSExecutionAdmissionError("PNCAP shadow grant generation mismatch")
    if capability != CAPABILITY:
        raise ApocalypOSExecutionAdmissionError("PNCAP shadow grant capability mismatch")
    if target_ref != TARGET_REF:
        raise ApocalypOSExecutionAdmissionError("PNCAP shadow grant target mismatch")
    if operation_ref != OPERATION_REF:
        raise ApocalypOSExecutionAdmissionError("PNCAP shadow grant operation mismatch")
    body = {
        "schema": GRANT_SCHEMA,
        "grant_id": _text(grant_id, "grant_id"),
        "capability": CAPABILITY,
        "principal_generation_id": principal,
        "environment_generation_id": environment,
        "target_ref": TARGET_REF,
        "operation_ref": OPERATION_REF,
        "physical_effect_authority": False,
        "production_runtime_write": False,
        "canon_allowed": False,
    }
    return _seal(body, "grant_sha256")


def validate_shadow_grant(grant: Mapping[str, Any]) -> None:
    if grant.get("schema") != GRANT_SCHEMA:
        raise ApocalypOSExecutionAdmissionError("PNCAP shadow grant schema mismatch")
    _verify_seal(grant, "grant_sha256")
    _text(grant.get("grant_id"), "grant_id")
    if grant.get("capability") != CAPABILITY:
        raise ApocalypOSExecutionAdmissionError("PNCAP shadow grant capability mismatch")
    principal = _text(grant.get("principal_generation_id"), "principal_generation_id")
    environment = _text(grant.get("environment_generation_id"), "environment_generation_id")
    if principal != environment:
        raise ApocalypOSExecutionAdmissionError("PNCAP shadow grant generation mismatch")
    if grant.get("target_ref") != TARGET_REF:
        raise ApocalypOSExecutionAdmissionError("PNCAP shadow grant target mismatch")
    if grant.get("operation_ref") != OPERATION_REF:
        raise ApocalypOSExecutionAdmissionError("PNCAP shadow grant operation mismatch")
    for key in ("physical_effect_authority", "production_runtime_write", "canon_allowed"):
        _must_be_false(grant, key)


def build_shadow_admission(
    *,
    semantic_loop_receipt: Mapping[str, Any],
    feedback_receipt: Mapping[str, Any],
    source_snapshot: Mapping[str, Any],
    replay_receipt: Mapping[str, Any],
    qemu_build_receipt: Mapping[str, Any],
    pncap_shadow_grant: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_semantic_loop_candidate(semantic_loop_receipt)
    try:
        validate_feedback_candidate_receipt(feedback_receipt)
    except Exception as exc:
        raise ApocalypOSExecutionAdmissionError(f"feedback candidate invalid: {exc}") from exc
    if semantic_loop_receipt.get("feedback_receipt_sha256") != feedback_receipt.get("feedback_receipt_sha256"):
        raise ApocalypOSExecutionAdmissionError("semantic loop/feedback parent mismatch")

    try:
        source_state = validate_source_snapshot(source_snapshot)
        validate_replay_receipt(replay_receipt, source_snapshot)
    except Exception as exc:
        raise ApocalypOSExecutionAdmissionError(f"source/replay validation failed: {exc}") from exc

    _validate_build_receipt(qemu_build_receipt, source_state=source_state, replay_receipt=replay_receipt)
    validate_shadow_grant(pncap_shadow_grant)

    body = {
        "schema": ADMISSION_SCHEMA,
        "semantic_loop_receipt_sha256": semantic_loop_receipt["loop_receipt_sha256"],
        "feedback_receipt_sha256": feedback_receipt["feedback_receipt_sha256"],
        "source_receipt_sha256": source_state["source_receipt_sha256"],
        "source_tick": source_state["tick"],
        "working_state_sha256": source_state["working_state_sha256"],
        "replay_receipt_sha256": replay_receipt["replay_receipt_sha256"],
        "replay_binary_sha256": qemu_build_receipt["replay_binary_sha256"],
        "qemu_build_receipt_sha256": qemu_build_receipt["receipt_sha256"],
        "qemu_rom_sha256": qemu_build_receipt["rom_sha256"],
        "pncap_grant_sha256": pncap_shadow_grant["grant_sha256"],
        "pncap_grant_id": pncap_shadow_grant["grant_id"],
        "principal_generation_id": pncap_shadow_grant["principal_generation_id"],
        "environment_generation_id": pncap_shadow_grant["environment_generation_id"],
        "capability": CAPABILITY,
        "target_ref": TARGET_REF,
        "operation_ref": OPERATION_REF,
        "shadow_execution_admitted": True,
        "production_execution_admitted": False,
        "physical_effect_authority": False,
        "production_runtime_write": False,
        "physical_qpu_claim": False,
        "physical_h200_execution_claim": False,
        "canon_allowed": False,
        "epistemic": EPISTEMIC,
    }
    return _seal(body, "admission_receipt_sha256")


def validate_shadow_admission(admission: Mapping[str, Any]) -> None:
    if admission.get("schema") != ADMISSION_SCHEMA:
        raise ApocalypOSExecutionAdmissionError("ApocalypOS admission schema mismatch")
    _verify_seal(admission, "admission_receipt_sha256")
    for key in (
        "semantic_loop_receipt_sha256",
        "feedback_receipt_sha256",
        "source_receipt_sha256",
        "working_state_sha256",
        "replay_receipt_sha256",
        "replay_binary_sha256",
        "qemu_build_receipt_sha256",
        "qemu_rom_sha256",
        "pncap_grant_sha256",
    ):
        _hex64(admission.get(key), key)
    _text(admission.get("pncap_grant_id"), "pncap_grant_id")
    principal = _text(admission.get("principal_generation_id"), "principal_generation_id")
    environment = _text(admission.get("environment_generation_id"), "environment_generation_id")
    if principal != environment:
        raise ApocalypOSExecutionAdmissionError("admission generation mismatch")
    if admission.get("capability") != CAPABILITY or admission.get("target_ref") != TARGET_REF or admission.get("operation_ref") != OPERATION_REF:
        raise ApocalypOSExecutionAdmissionError("admission capability/target/operation mismatch")
    if admission.get("shadow_execution_admitted") is not True:
        raise ApocalypOSExecutionAdmissionError("shadow execution was not admitted")
    for key in (
        "production_execution_admitted",
        "physical_effect_authority",
        "production_runtime_write",
        "physical_qpu_claim",
        "physical_h200_execution_claim",
        "canon_allowed",
    ):
        _must_be_false(admission, key)
    if admission.get("epistemic") != EPISTEMIC:
        raise ApocalypOSExecutionAdmissionError("admission epistemic state mismatch")


def _validate_qemu_conformance(
    conformance: Mapping[str, Any],
    *,
    admission: Mapping[str, Any],
) -> None:
    if conformance.get("schema") != QEMU_CONFORMANCE_SCHEMA:
        raise ApocalypOSExecutionAdmissionError("QEMU conformance schema mismatch")
    _verify_seal(conformance, "receipt_sha256")
    if conformance.get("status") != QEMU_PASS_STATUS or conformance.get("reason") is not None:
        raise ApocalypOSExecutionAdmissionError("QEMU replay did not pass")
    if conformance.get("qemu_executed") is not True:
        raise ApocalypOSExecutionAdmissionError("QEMU replay receipt does not prove execution")
    if conformance.get("expected_sequence_present") is not True:
        raise ApocalypOSExecutionAdmissionError("QEMU expected replay sequence missing")
    if conformance.get("failure_marker_present") is not False:
        raise ApocalypOSExecutionAdmissionError("QEMU failure marker present")
    for key in (
        "runtime_execution_authority",
        "canon_write_authority",
        "physical_h200_execution_claim",
        "physical_qpu_claim",
        "physical_machine_claim",
    ):
        _must_be_false(conformance, key)
    if conformance.get("source_receipt_sha256") != admission.get("source_receipt_sha256"):
        raise ApocalypOSExecutionAdmissionError("conformance/source lineage mismatch")
    if conformance.get("working_state_sha256") != admission.get("working_state_sha256"):
        raise ApocalypOSExecutionAdmissionError("conformance/working-state lineage mismatch")
    if conformance.get("source_tick") != admission.get("source_tick"):
        raise ApocalypOSExecutionAdmissionError("conformance/tick lineage mismatch")
    if conformance.get("replay_binary_sha256") != admission.get("replay_binary_sha256"):
        raise ApocalypOSExecutionAdmissionError("conformance/replay binary lineage mismatch")
    if conformance.get("build_receipt_sha256") != admission.get("qemu_build_receipt_sha256"):
        raise ApocalypOSExecutionAdmissionError("conformance/build lineage mismatch")


def build_execution_result(
    admission_receipt: Mapping[str, Any],
    qemu_conformance_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    validate_shadow_admission(admission_receipt)
    _validate_qemu_conformance(qemu_conformance_receipt, admission=admission_receipt)
    body = {
        "schema": RESULT_SCHEMA,
        "admission_receipt_sha256": admission_receipt["admission_receipt_sha256"],
        "qemu_conformance_receipt_sha256": qemu_conformance_receipt["receipt_sha256"],
        "source_receipt_sha256": admission_receipt["source_receipt_sha256"],
        "source_tick": admission_receipt["source_tick"],
        "working_state_sha256": admission_receipt["working_state_sha256"],
        "replay_binary_sha256": admission_receipt["replay_binary_sha256"],
        "qemu_build_receipt_sha256": admission_receipt["qemu_build_receipt_sha256"],
        "execution_observed": True,
        "shadow_execution_only": True,
        "production_execution_admitted": False,
        "physical_effect_authority": False,
        "production_runtime_write": False,
        "physical_qpu_claim": False,
        "physical_h200_execution_claim": False,
        "canon_allowed": False,
        "epistemic": EPISTEMIC,
    }
    return _seal(body, "execution_result_sha256")


def validate_execution_result(result: Mapping[str, Any]) -> None:
    if result.get("schema") != RESULT_SCHEMA:
        raise ApocalypOSExecutionAdmissionError("ApocalypOS execution result schema mismatch")
    _verify_seal(result, "execution_result_sha256")
    for key in (
        "admission_receipt_sha256",
        "qemu_conformance_receipt_sha256",
        "source_receipt_sha256",
        "working_state_sha256",
        "replay_binary_sha256",
        "qemu_build_receipt_sha256",
    ):
        _hex64(result.get(key), key)
    if result.get("execution_observed") is not True or result.get("shadow_execution_only") is not True:
        raise ApocalypOSExecutionAdmissionError("execution result is not a bounded observed shadow execution")
    for key in (
        "production_execution_admitted",
        "physical_effect_authority",
        "production_runtime_write",
        "physical_qpu_claim",
        "physical_h200_execution_claim",
        "canon_allowed",
    ):
        _must_be_false(result, key)
    if result.get("epistemic") != EPISTEMIC:
        raise ApocalypOSExecutionAdmissionError("execution result epistemic state mismatch")


def build_noema_reintegration_candidate(
    execution_result: Mapping[str, Any],
    *,
    observed_state_commitment: str,
    qhtri_next_target_ref: str,
) -> dict[str, Any]:
    validate_execution_result(execution_result)
    body = {
        "schema": REINTEGRATION_SCHEMA,
        "execution_result_sha256": execution_result["execution_result_sha256"],
        "source_receipt_sha256": execution_result["source_receipt_sha256"],
        "source_tick": execution_result["source_tick"],
        "working_state_sha256": execution_result["working_state_sha256"],
        "observed_state_commitment": _hex64(observed_state_commitment, "observed_state_commitment"),
        "qhtri_next_target_ref": _text(qhtri_next_target_ref, "qhtri_next_target_ref"),
        "evidence_class": "MEASURED_EMULATION_RESULT",
        "candidate_only": True,
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "production_runtime_write": False,
        "physical_qpu_claim": False,
        "physical_h200_execution_claim": False,
        "epistemic": EPISTEMIC,
    }
    return _seal(body, "reintegration_receipt_sha256")


def validate_noema_reintegration_candidate(receipt: Mapping[str, Any]) -> None:
    if receipt.get("schema") != REINTEGRATION_SCHEMA:
        raise ApocalypOSExecutionAdmissionError("NOEMA reintegration schema mismatch")
    _verify_seal(receipt, "reintegration_receipt_sha256")
    for key in (
        "execution_result_sha256",
        "source_receipt_sha256",
        "working_state_sha256",
        "observed_state_commitment",
    ):
        _hex64(receipt.get(key), key)
    _text(receipt.get("qhtri_next_target_ref"), "qhtri_next_target_ref")
    if receipt.get("evidence_class") != "MEASURED_EMULATION_RESULT" or receipt.get("candidate_only") is not True:
        raise ApocalypOSExecutionAdmissionError("reintegration is not a measured candidate-only result")
    for key in (
        "runtime_execution_authority",
        "canon_write_authority",
        "production_runtime_write",
        "physical_qpu_claim",
        "physical_h200_execution_claim",
    ):
        _must_be_false(receipt, key)
    if receipt.get("epistemic") != EPISTEMIC:
        raise ApocalypOSExecutionAdmissionError("reintegration epistemic state mismatch")
