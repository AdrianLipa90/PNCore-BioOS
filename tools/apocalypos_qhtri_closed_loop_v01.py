from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

from tools.apocalypos_qhtri_execution_admission_v01 import (
    build_execution_result,
    build_noema_reintegration_candidate,
    build_shadow_admission,
    build_shadow_grant,
    validate_execution_result,
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
    validate_loop_receipt,
)
from tools.vector_native_qhtri_replay_v01 import (
    validate_replay_receipt,
    validate_source_snapshot,
)

BANK_PIN_SCHEMA = "BIOOS_GREMLIN_NOEMA_QHTRI_BANK_PIN_V0_1"
SEMANTIC_BUNDLE_SCHEMA = "BIOOS_APOCALYPOS_QHTRI_SEMANTIC_BUNDLE_V0_1"
NEXT_CANDIDATE_SCHEMA = "BIOOS_QHTRI_NEXT_STATE_CANDIDATE_V0_1"
CLOSED_LOOP_SCHEMA = "BIOOS_APOCALYPOS_QHTRI_CLOSED_LOOP_V0_1"
EPISTEMIC = "CHYBA"


class ClosedLoopError(RuntimeError):
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


def _seal(body: Mapping[str, Any], key: str) -> dict[str, Any]:
    if key in body:
        raise ClosedLoopError(f"seal key already present: {key}")
    out = dict(body)
    out[key] = _sha256(body)
    return out


def _verify_seal(value: Mapping[str, Any], key: str) -> None:
    recorded = str(value.get(key, ""))
    if len(recorded) != 64:
        raise ClosedLoopError(f"missing or malformed seal: {key}")
    try:
        bytes.fromhex(recorded)
    except ValueError as exc:
        raise ClosedLoopError(f"malformed seal: {key}") from exc
    body = {name: item for name, item in value.items() if name != key}
    if _sha256(body) != recorded:
        raise ClosedLoopError(f"seal mismatch: {key}")


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ClosedLoopError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ClosedLoopError(f"JSON root must be an object: {path}")
    return value


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hex64(value: Any, name: str) -> str:
    text = str(value).lower()
    if len(text) != 64:
        raise ClosedLoopError(f"{name} must be 64 hex characters")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise ClosedLoopError(f"{name} must be hexadecimal") from exc
    return text


def _finite(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ClosedLoopError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise ClosedLoopError(f"{name} must be finite")
    return number


def validate_bank_pin(pin: Mapping[str, Any]) -> str:
    if pin.get("schema") != BANK_PIN_SCHEMA:
        raise ClosedLoopError("GREMLIN/NOEMA/QHTRI bank pin schema mismatch")
    if pin.get("bank_entry_count") != len(FULL_BANK_ISOMORPHISM_IDS):
        raise ClosedLoopError("GREMLIN bank entry count mismatch")
    if pin.get("promotion_state") != "CANDIDATE_ONLY" or pin.get("epistemic") != EPISTEMIC:
        raise ClosedLoopError("GREMLIN bank pin epistemic boundary mismatch")
    for key in ("runtime_execution_authority", "canon_write_authority"):
        if pin.get(key) is not False:
            raise ClosedLoopError(f"GREMLIN bank pin authority boundary open: {key}")
    for key in (
        "bank_repository",
        "bank_branch",
        "bank_head_commit",
        "bank_spec_path",
        "bank_implementation_path",
    ):
        if not str(pin.get(key, "")).strip():
            raise ClosedLoopError(f"GREMLIN bank pin missing {key}")
    return _sha256(pin)


def build_semantic_bundle(
    source: Mapping[str, Any],
    replay: Mapping[str, Any],
    bank_pin: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        state = validate_source_snapshot(source)
        validate_replay_receipt(replay, source)
    except Exception as exc:
        raise ClosedLoopError(f"source/replay validation failed: {exc}") from exc
    bank_manifest = validate_bank_pin(bank_pin)

    edge = source.get("selected_edge")
    surface = source.get("surface_state")
    holonomy = source.get("holonomy")
    if not isinstance(edge, Mapping) or not isinstance(surface, Mapping):
        raise ClosedLoopError("source snapshot lacks selected_edge or surface_state")
    if not isinstance(holonomy, list) or len(holonomy) < 6:
        raise ClosedLoopError("source snapshot lacks a usable holonomy witness")
    if surface.get("noema_tick") != state["tick"]:
        raise ClosedLoopError("source surface tick does not match source tick")

    i = int(edge.get("oscillator_i", -1))
    j = int(edge.get("oscillator_j", -1))
    if i != state["oscillator_i"] or j != state["oscillator_j"]:
        raise ClosedLoopError("source selected edge does not match validated replay edge")

    sheet_value = _finite(holonomy[5], "holonomy[5]")
    if abs(abs(sheet_value) - 1.0) > 1e-12:
        raise ClosedLoopError("holonomy witness does not provide an exact +/-1 spinor sheet")
    spinor_sheet = 1 if sheet_value > 0.0 else -1

    poincare = edge.get("poincare_i")
    if not isinstance(poincare, list) or len(poincare) != 2:
        raise ClosedLoopError("selected edge lacks Poincare anchor")

    source_receipt = state["source_receipt_sha256"]
    source_document_sha256 = _sha256(source)
    replay_document_sha256 = _sha256(replay)

    bifurcation = build_bifurcation_receipt(
        bank_manifest_sha256=bank_manifest,
        qhtri_tick=state["tick"],
        qhtri_state_commitment=source_receipt,
        magnitude_M=abs(_finite(edge.get("coupling"), "selected_edge.coupling")),
        beta=_finite(surface.get("psi_global"), "surface_state.psi_global"),
        generator_ref=(
            f"QHTRI.EDGE.{i}.{j}:"
            f"{str(edge.get('selection_rule', 'UNSPECIFIED')).strip() or 'UNSPECIFIED'}"
        ),
        t36_witness_commitment=_hex64(source.get("phi_raw_sha256"), "phi_raw_sha256"),
        cp1_state_commitment=_hex64(source.get("R_geom_raw_sha256"), "R_geom_raw_sha256"),
        telemetry_evidence_ref=(
            f"{str(source.get('surface_root', '')).strip()}:tick={state['tick']};"
            f"source_receipt={source_receipt}"
        ),
    )
    anchor = build_projective_anchor_receipt(
        bifurcation,
        poincare_re=_finite(poincare[0], "poincare_i[0]"),
        poincare_im=_finite(poincare[1], "poincare_i[1]"),
        spinor_sheet=spinor_sheet,
        cp1_poincare_adapter_commitment=_hex64(
            source.get("psi_geom_raw_sha256"), "psi_geom_raw_sha256"
        ),
        holonomy_audit_commitment=_hex64(
            source.get("holonomy_raw_sha256"), "holonomy_raw_sha256"
        ),
    )
    semantic_path = build_semantic_path_receipt(
        (anchor,),
        ordered_relation_ids=(),
        ordered_kaku_candidate_ids=(f"KAKU.SOURCE.TICK.{state['tick']}",),
        ordered_radical_candidate_ids=(f"RADICAL.EDGE.{i}.{j}",),
        ordered_operator_candidate_ids=(
            "OP.APOCALYPOS.SHADOW_QEMU",
            "OP.NOEMA.REINTEGRATE_QHTRI_CANDIDATE",
        ),
        gremlin_isomorphism_ids=FULL_BANK_ISOMORPHISM_IDS,
    )
    state_crystal = build_state_crystal_receipt(
        semantic_path,
        state_object_id=f"STATE.QHTRI.TICK.{state['tick']}",
        pnfs_object_id=f"PNFS.QHTRI.TICK.{state['tick']}",
        generation=state["tick"],
        memory_epoch=state["tick"],
        checkpoint_commitment=state["working_state_sha256"],
        identity_layer_mutation=False,
    )
    feedback = build_feedback_candidate_receipt(
        state_crystal,
        hermitian_operator_commitment=_hex64(
            replay.get("replay_binary_sha256"), "replay_binary_sha256"
        ),
        pncap_admission_token=f"PNCAP.CANDIDATE.TICK.{state['tick']}.QEMU",
        qhtri_target_ref="QHTRI.NEXT.CANDIDATE",
    )
    loop = build_loop_receipt(
        bifurcation_receipt=bifurcation,
        anchor_receipt=anchor,
        semantic_path_receipt=semantic_path,
        state_crystal_receipt=state_crystal,
        feedback_receipt=feedback,
        require_full_bank=True,
    )
    validate_loop_receipt(
        loop,
        bifurcation_receipt=bifurcation,
        anchor_receipt=anchor,
        semantic_path_receipt=semantic_path,
        state_crystal_receipt=state_crystal,
        feedback_receipt=feedback,
    )

    body = {
        "schema": SEMANTIC_BUNDLE_SCHEMA,
        "source_tick": state["tick"],
        "source_receipt_sha256": source_receipt,
        "source_document_sha256": source_document_sha256,
        "replay_document_sha256": replay_document_sha256,
        "bank_pin_document_sha256": bank_manifest,
        "bank_head_commit": bank_pin["bank_head_commit"],
        "bifurcation": bifurcation,
        "anchor": anchor,
        "semantic_path": semantic_path,
        "state_crystal": state_crystal,
        "feedback": feedback,
        "semantic_loop": loop,
        "candidate_only": True,
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "production_runtime_write": False,
        "epistemic": EPISTEMIC,
    }
    return _seal(body, "semantic_bundle_sha256")


def validate_semantic_bundle(
    bundle: Mapping[str, Any],
    source: Mapping[str, Any],
    replay: Mapping[str, Any],
    bank_pin: Mapping[str, Any],
) -> None:
    if bundle.get("schema") != SEMANTIC_BUNDLE_SCHEMA:
        raise ClosedLoopError("semantic bundle schema mismatch")
    _verify_seal(bundle, "semantic_bundle_sha256")
    if bundle.get("source_document_sha256") != _sha256(source):
        raise ClosedLoopError("semantic bundle/source document mismatch")
    if bundle.get("replay_document_sha256") != _sha256(replay):
        raise ClosedLoopError("semantic bundle/replay document mismatch")
    if bundle.get("bank_pin_document_sha256") != validate_bank_pin(bank_pin):
        raise ClosedLoopError("semantic bundle/bank pin mismatch")
    for key in ("runtime_execution_authority", "canon_write_authority", "production_runtime_write"):
        if bundle.get(key) is not False:
            raise ClosedLoopError(f"semantic bundle authority boundary open: {key}")
    if bundle.get("candidate_only") is not True or bundle.get("epistemic") != EPISTEMIC:
        raise ClosedLoopError("semantic bundle candidate/epistemic boundary mismatch")
    validate_loop_receipt(
        bundle["semantic_loop"],
        bifurcation_receipt=bundle["bifurcation"],
        anchor_receipt=bundle["anchor"],
        semantic_path_receipt=bundle["semantic_path"],
        state_crystal_receipt=bundle["state_crystal"],
        feedback_receipt=bundle["feedback"],
    )


def build_preexecution_chain(
    source: Mapping[str, Any],
    replay: Mapping[str, Any],
    bank_pin: Mapping[str, Any],
    qemu_build: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    bundle = build_semantic_bundle(source, replay, bank_pin)
    validate_semantic_bundle(bundle, source, replay, bank_pin)
    state = validate_source_snapshot(source)
    generation_id = state["working_state_sha256"]
    grant = build_shadow_grant(
        principal_generation_id=generation_id,
        environment_generation_id=generation_id,
        grant_id=f"APOCALYPOS.SHADOW.QEMU.TICK.{state['tick']}.{state['source_receipt_sha256'][:16]}",
    )
    validate_shadow_grant(grant)
    try:
        admission = build_shadow_admission(
            semantic_loop_receipt=bundle["semantic_loop"],
            feedback_receipt=bundle["feedback"],
            source_snapshot=source,
            replay_receipt=replay,
            qemu_build_receipt=qemu_build,
            pncap_shadow_grant=grant,
        )
        validate_shadow_admission(admission)
    except Exception as exc:
        raise ClosedLoopError(f"ApocalypOS pre-execution admission failed: {exc}") from exc
    return bundle, grant, admission


def build_next_qhtri_candidate(
    source: Mapping[str, Any],
    reintegration: Mapping[str, Any],
    qemu_conformance: Mapping[str, Any],
) -> dict[str, Any]:
    state = validate_source_snapshot(source)
    validate_noema_reintegration_candidate(reintegration)
    observed = _hex64(qemu_conformance.get("receipt_sha256"), "qemu conformance receipt")
    if reintegration.get("observed_state_commitment") != observed:
        raise ClosedLoopError("reintegration does not bind the actual QEMU observation")
    body = {
        "schema": NEXT_CANDIDATE_SCHEMA,
        "source_tick": state["tick"],
        "proposed_tick": state["tick"] + 1,
        "source_receipt_sha256": state["source_receipt_sha256"],
        "source_vector_commitment": _hex64(source.get("phi_raw_sha256"), "phi_raw_sha256"),
        "execution_observation_commitment": observed,
        "reintegration_receipt_sha256": reintegration["reintegration_receipt_sha256"],
        "transition_semantics": "PROVENANCE_ONLY_NO_DYNAMICAL_UPDATE_CLAIM",
        "vector_update_policy": "EXTERNAL_QHTRI_UPDATER_REQUIRED",
        "candidate_only": True,
        "runtime_write": False,
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "production_runtime_write": False,
        "physical_qpu_claim": False,
        "physical_h200_execution_claim": False,
        "epistemic": EPISTEMIC,
    }
    return _seal(body, "next_candidate_sha256")


def build_postexecution_chain(
    source: Mapping[str, Any],
    replay: Mapping[str, Any],
    bank_pin: Mapping[str, Any],
    qemu_build: Mapping[str, Any],
    semantic_bundle: Mapping[str, Any],
    grant: Mapping[str, Any],
    admission: Mapping[str, Any],
    qemu_conformance: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    validate_semantic_bundle(semantic_bundle, source, replay, bank_pin)
    validate_shadow_grant(grant)
    validate_shadow_admission(admission)

    if admission.get("semantic_loop_receipt_sha256") != semantic_bundle["semantic_loop"]["loop_receipt_sha256"]:
        raise ClosedLoopError("admission/semantic-loop mismatch")
    if admission.get("feedback_receipt_sha256") != semantic_bundle["feedback"]["feedback_receipt_sha256"]:
        raise ClosedLoopError("admission/feedback mismatch")
    if admission.get("qemu_build_receipt_sha256") != qemu_build.get("receipt_sha256"):
        raise ClosedLoopError("admission/build mismatch")
    if admission.get("pncap_grant_sha256") != grant.get("grant_sha256"):
        raise ClosedLoopError("admission/PNCAP grant mismatch")

    try:
        execution_result = build_execution_result(admission, qemu_conformance)
        validate_execution_result(execution_result)
        reintegration = build_noema_reintegration_candidate(
            execution_result,
            observed_state_commitment=_hex64(
                qemu_conformance.get("receipt_sha256"), "qemu conformance receipt"
            ),
            qhtri_next_target_ref="QHTRI.NEXT.CANDIDATE",
        )
        validate_noema_reintegration_candidate(reintegration)
    except Exception as exc:
        raise ClosedLoopError(f"ApocalypOS post-execution reintegration failed: {exc}") from exc

    next_candidate = build_next_qhtri_candidate(source, reintegration, qemu_conformance)
    state = validate_source_snapshot(source)
    body = {
        "schema": CLOSED_LOOP_SCHEMA,
        "status": "PASS_CLOSED_VECTOR_NATIVE_SHADOW_LOOP",
        "source_tick": state["tick"],
        "source_receipt_sha256": state["source_receipt_sha256"],
        "source_document_sha256": _sha256(source),
        "replay_receipt_sha256": replay["replay_receipt_sha256"],
        "semantic_bundle_sha256": semantic_bundle["semantic_bundle_sha256"],
        "semantic_loop_receipt_sha256": semantic_bundle["semantic_loop"]["loop_receipt_sha256"],
        "pncap_grant_sha256": grant["grant_sha256"],
        "apocalypos_admission_receipt_sha256": admission["admission_receipt_sha256"],
        "qemu_build_receipt_sha256": qemu_build["receipt_sha256"],
        "qemu_conformance_receipt_sha256": qemu_conformance["receipt_sha256"],
        "execution_result_sha256": execution_result["execution_result_sha256"],
        "reintegration_receipt_sha256": reintegration["reintegration_receipt_sha256"],
        "next_qhtri_candidate_sha256": next_candidate["next_candidate_sha256"],
        "ordered_stages": [
            "LIVE_QHTRI_SOURCE_SNAPSHOT",
            "NOEMA_SEMANTIC_CANDIDATE",
            "APOCALYPOS_PNCAP_SHADOW_GRANT",
            "APOCALYPOS_PRE_EXECUTION_ADMISSION",
            "QEMU_TCG_BINARY_REALIZATION",
            "APOCALYPOS_MEASURED_EXECUTION_RESULT",
            "NOEMA_REINTEGRATION_CANDIDATE",
            "QHTRI_NEXT_STATE_CANDIDATE",
        ],
        "binary_realization_adapter": "QEMU_TCG",
        "shadow_execution_only": True,
        "vector_native_source": True,
        "candidate_only": True,
        "runtime_write": False,
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "production_runtime_write": False,
        "physical_machine_claim": False,
        "physical_qpu_claim": False,
        "physical_h200_execution_claim": False,
        "epistemic": EPISTEMIC,
    }
    manifest = _seal(body, "closed_loop_receipt_sha256")
    return execution_result, reintegration, next_candidate, manifest


def _paths(root: Path) -> dict[str, Path]:
    p = root / "provenance"
    return {
        "source": p / "BIOOS_VECTOR_NATIVE_QHTRI_SOURCE_V0_1.json",
        "replay": p / "BIOOS_VECTOR_NATIVE_QHTRI_REPLAY_V0_1.json",
        "bank": p / "GREMLIN_NOEMA_QHTRI_BANK_PIN_V0_1.json",
        "build": p / "BIOOS_VECTOR_NATIVE_QHTRI_QEMU_BUILD_V0_1.json",
        "conformance": p / "BIOOS_VECTOR_NATIVE_QHTRI_QEMU_CONFORMANCE_V0_1.json",
        "bundle": p / "BIOOS_APOCALYPOS_QHTRI_SEMANTIC_BUNDLE_V0_1.json",
        "grant": p / "BIOOS_APOCALYPOS_PNCAP_SHADOW_GRANT_V0_1.json",
        "admission": p / "BIOOS_APOCALYPOS_QHTRI_ADMISSION_V0_1.json",
        "result": p / "BIOOS_APOCALYPOS_QHTRI_EXECUTION_RESULT_V0_1.json",
        "reintegration": p / "BIOOS_NOEMA_QHTRI_REINTEGRATION_CANDIDATE_V0_1.json",
        "next": p / "BIOOS_QHTRI_NEXT_STATE_CANDIDATE_V0_1.json",
        "manifest": p / "BIOOS_APOCALYPOS_QHTRI_CLOSED_LOOP_V0_1.json",
    }


def pre(root: Path) -> dict[str, Any]:
    paths = _paths(root)
    source = _load(paths["source"])
    replay = _load(paths["replay"])
    bank = _load(paths["bank"])
    build = _load(paths["build"])
    bundle, grant, admission = build_preexecution_chain(source, replay, bank, build)
    _write(paths["bundle"], bundle)
    _write(paths["grant"], grant)
    _write(paths["admission"], admission)
    return {
        "status": "PASS_APOCALYPOS_PRE_EXECUTION_ADMISSION",
        "semantic_bundle_sha256": bundle["semantic_bundle_sha256"],
        "pncap_grant_sha256": grant["grant_sha256"],
        "admission_receipt_sha256": admission["admission_receipt_sha256"],
        "shadow_execution_admitted": True,
        "production_execution_admitted": False,
        "epistemic": EPISTEMIC,
    }


def post(root: Path) -> dict[str, Any]:
    paths = _paths(root)
    source = _load(paths["source"])
    replay = _load(paths["replay"])
    bank = _load(paths["bank"])
    build = _load(paths["build"])
    bundle = _load(paths["bundle"])
    grant = _load(paths["grant"])
    admission = _load(paths["admission"])
    conformance = _load(paths["conformance"])
    result, reintegration, next_candidate, manifest = build_postexecution_chain(
        source,
        replay,
        bank,
        build,
        bundle,
        grant,
        admission,
        conformance,
    )
    _write(paths["result"], result)
    _write(paths["reintegration"], reintegration)
    _write(paths["next"], next_candidate)
    _write(paths["manifest"], manifest)
    return {
        "status": manifest["status"],
        "closed_loop_receipt_sha256": manifest["closed_loop_receipt_sha256"],
        "execution_result_sha256": result["execution_result_sha256"],
        "reintegration_receipt_sha256": reintegration["reintegration_receipt_sha256"],
        "next_qhtri_candidate_sha256": next_candidate["next_candidate_sha256"],
        "runtime_write": False,
        "epistemic": EPISTEMIC,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a receipt-closed ApocalypOS/QHTRI QEMU shadow loop")
    ap.add_argument("stage", choices=("pre", "post"))
    ap.add_argument("repo_root", type=Path, nargs="?", default=Path("."))
    args = ap.parse_args()
    root = args.repo_root.resolve()
    try:
        payload = pre(root) if args.stage == "pre" else post(root)
    except Exception as exc:
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "stage": args.stage,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }, indent=2, sort_keys=True))
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
