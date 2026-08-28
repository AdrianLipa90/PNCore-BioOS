from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping, Sequence

BIFURCATION_SCHEMA = "BIOOS-NOEMA-QHTRI-BIFURCATION/0.1"
ANCHOR_SCHEMA = "BIOOS-NOEMA-QHTRI-PROJECTIVE-ANCHOR/0.1"
SEMANTIC_PATH_SCHEMA = "BIOOS-NOEMA-QHTRI-SEMANTIC-PATH/0.1"
STATE_CRYSTAL_SCHEMA = "BIOOS-NOEMA-QHTRI-STATE-CRYSTAL/0.1"
FEEDBACK_SCHEMA = "BIOOS-NOEMA-QHTRI-FEEDBACK-CANDIDATE/0.1"
LOOP_SCHEMA = "BIOOS-NOEMA-QHTRI-SEMANTIC-LOOP/0.1"

SOURCE_CLASS = "NATURAL_SYSTEM_STATE"
DYNAMICS_CLASS = "ENDOGENOUS_RUNTIME_DYNAMICS"
EFFECT_POLICY = "OPERATOR_BINDABLE"

FULL_BANK_ISOMORPHISM_IDS = (
    "ISO.NQ.01.CP1.BERRY.QHTRI.POTENTIAL",
    "ISO.NQ.02.IDT.BIFURCATION.NQ.RECEIPT",
    "ISO.NQ.03.CP1.POINCARE.CONTINUATION",
    "ISO.NQ.04.SPINOR.SHEET.WITNESS",
    "ISO.NQ.05.AFFINITY.SEMANTIC.ORIENTATION",
    "ISO.NQ.06.MEMORY.ORBIT.MEANING.PATH",
    "ISO.NQ.07.HOLONOMY.BRANCH.CHANNELS",
    "ISO.NQ.08.COFRAME.QHTRI.CELL.TRANSPORT",
    "ISO.NQ.09.MEMORY.STATE.CRYSTALLIZATION",
    "ISO.NQ.10.NOEMA.QHTRI.HERMITIAN.FEEDBACK",
)


class NoemaQhtriSemanticLoopError(RuntimeError):
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


def _seal(body: Mapping[str, Any], hash_key: str) -> dict[str, Any]:
    if hash_key in body:
        raise NoemaQhtriSemanticLoopError(f"hash key already present: {hash_key}")
    sealed = dict(body)
    sealed[hash_key] = _sha256(body)
    return sealed


def _verify_seal(value: Mapping[str, Any], hash_key: str) -> None:
    if hash_key not in value:
        raise NoemaQhtriSemanticLoopError(f"missing seal: {hash_key}")
    body = {key: item for key, item in value.items() if key != hash_key}
    expected = _sha256(body)
    if value[hash_key] != expected:
        raise NoemaQhtriSemanticLoopError(f"seal mismatch: {hash_key}")


def _require_hex64(value: Any, name: str) -> str:
    text = str(value)
    if len(text) != 64:
        raise NoemaQhtriSemanticLoopError(f"{name} must be 64 hex characters")
    try:
        bytes.fromhex(text)
    except ValueError as exc:
        raise NoemaQhtriSemanticLoopError(f"{name} must be hexadecimal") from exc
    return text.lower()


def _require_text(value: Any, name: str) -> str:
    text = str(value).strip()
    if not text:
        raise NoemaQhtriSemanticLoopError(f"{name} is required")
    return text


def _require_finite(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise NoemaQhtriSemanticLoopError(f"{name} must be numeric") from exc
    if not math.isfinite(number):
        raise NoemaQhtriSemanticLoopError(f"{name} must be finite")
    return number


def _require_nonnegative_int(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise NoemaQhtriSemanticLoopError(f"{name} must be an integer")
    try:
        integer = int(value)
    except (TypeError, ValueError) as exc:
        raise NoemaQhtriSemanticLoopError(f"{name} must be an integer") from exc
    if integer != value or integer < 0:
        raise NoemaQhtriSemanticLoopError(f"{name} must be a non-negative integer")
    return integer


def _require_bank_subset(values: Sequence[str]) -> tuple[str, ...]:
    ids = tuple(_require_text(value, "gremlin_isomorphism_id") for value in values)
    if len(ids) != len(set(ids)):
        raise NoemaQhtriSemanticLoopError("duplicate GREMLIN isomorphism id")
    positions = []
    for iso_id in ids:
        if iso_id not in FULL_BANK_ISOMORPHISM_IDS:
            raise NoemaQhtriSemanticLoopError(f"unknown GREMLIN isomorphism id: {iso_id}")
        positions.append(FULL_BANK_ISOMORPHISM_IDS.index(iso_id))
    if positions != sorted(positions):
        raise NoemaQhtriSemanticLoopError("GREMLIN isomorphism ids must preserve bank order")
    return ids


def build_bifurcation_receipt(
    *,
    bank_manifest_sha256: str,
    qhtri_tick: int,
    qhtri_state_commitment: str,
    magnitude_M: float,
    beta: float,
    generator_ref: str,
    t36_witness_commitment: str,
    cp1_state_commitment: str,
    telemetry_evidence_ref: str,
) -> dict[str, Any]:
    magnitude = _require_finite(magnitude_M, "magnitude_M")
    if magnitude < 0.0:
        raise NoemaQhtriSemanticLoopError("magnitude_M must be non-negative")
    body = {
        "schema": BIFURCATION_SCHEMA,
        "bank_manifest_sha256": _require_hex64(bank_manifest_sha256, "bank_manifest_sha256"),
        "qhtri_tick": _require_nonnegative_int(qhtri_tick, "qhtri_tick"),
        "qhtri_state_commitment": _require_hex64(qhtri_state_commitment, "qhtri_state_commitment"),
        "magnitude_M": magnitude,
        "beta": _require_finite(beta, "beta"),
        "generator_ref": _require_text(generator_ref, "generator_ref"),
        "t36_witness_commitment": _require_hex64(t36_witness_commitment, "t36_witness_commitment"),
        "cp1_state_commitment": _require_hex64(cp1_state_commitment, "cp1_state_commitment"),
        "telemetry_evidence_ref": _require_text(telemetry_evidence_ref, "telemetry_evidence_ref"),
        "source_class": SOURCE_CLASS,
        "dynamics_class": DYNAMICS_CLASS,
    }
    return _seal(body, "bifurcation_receipt_sha256")


def validate_bifurcation_receipt(receipt: Mapping[str, Any]) -> None:
    if receipt.get("schema") != BIFURCATION_SCHEMA:
        raise NoemaQhtriSemanticLoopError("invalid bifurcation schema")
    _require_hex64(receipt.get("bank_manifest_sha256"), "bank_manifest_sha256")
    _require_nonnegative_int(receipt.get("qhtri_tick"), "qhtri_tick")
    _require_hex64(receipt.get("qhtri_state_commitment"), "qhtri_state_commitment")
    magnitude = _require_finite(receipt.get("magnitude_M"), "magnitude_M")
    if magnitude < 0.0:
        raise NoemaQhtriSemanticLoopError("magnitude_M must be non-negative")
    _require_finite(receipt.get("beta"), "beta")
    _require_text(receipt.get("generator_ref"), "generator_ref")
    _require_hex64(receipt.get("t36_witness_commitment"), "t36_witness_commitment")
    _require_hex64(receipt.get("cp1_state_commitment"), "cp1_state_commitment")
    _require_text(receipt.get("telemetry_evidence_ref"), "telemetry_evidence_ref")
    if receipt.get("source_class") != SOURCE_CLASS:
        raise NoemaQhtriSemanticLoopError("QHTRI source class mismatch")
    if receipt.get("dynamics_class") != DYNAMICS_CLASS:
        raise NoemaQhtriSemanticLoopError("QHTRI dynamics class mismatch")
    _verify_seal(receipt, "bifurcation_receipt_sha256")


def build_projective_anchor_receipt(
    bifurcation_receipt: Mapping[str, Any],
    *,
    poincare_re: float,
    poincare_im: float,
    spinor_sheet: int,
    cp1_poincare_adapter_commitment: str,
    holonomy_audit_commitment: str,
) -> dict[str, Any]:
    validate_bifurcation_receipt(bifurcation_receipt)
    re = _require_finite(poincare_re, "poincare_re")
    im = _require_finite(poincare_im, "poincare_im")
    if re * re + im * im >= 1.0:
        raise NoemaQhtriSemanticLoopError("Poincare anchor must lie inside the unit disk")
    if spinor_sheet not in (-1, 1):
        raise NoemaQhtriSemanticLoopError("spinor_sheet must be -1 or +1")
    body = {
        "schema": ANCHOR_SCHEMA,
        "bank_manifest_sha256": bifurcation_receipt["bank_manifest_sha256"],
        "bifurcation_receipt_sha256": bifurcation_receipt["bifurcation_receipt_sha256"],
        "poincare_re": re,
        "poincare_im": im,
        "spinor_sheet": int(spinor_sheet),
        "cp1_poincare_adapter_commitment": _require_hex64(
            cp1_poincare_adapter_commitment, "cp1_poincare_adapter_commitment"
        ),
        "holonomy_audit_commitment": _require_hex64(
            holonomy_audit_commitment, "holonomy_audit_commitment"
        ),
    }
    return _seal(body, "anchor_receipt_sha256")


def validate_projective_anchor_receipt(receipt: Mapping[str, Any]) -> None:
    if receipt.get("schema") != ANCHOR_SCHEMA:
        raise NoemaQhtriSemanticLoopError("invalid projective anchor schema")
    _require_hex64(receipt.get("bank_manifest_sha256"), "bank_manifest_sha256")
    _require_hex64(receipt.get("bifurcation_receipt_sha256"), "bifurcation_receipt_sha256")
    re = _require_finite(receipt.get("poincare_re"), "poincare_re")
    im = _require_finite(receipt.get("poincare_im"), "poincare_im")
    if re * re + im * im >= 1.0:
        raise NoemaQhtriSemanticLoopError("Poincare anchor must lie inside the unit disk")
    if receipt.get("spinor_sheet") not in (-1, 1):
        raise NoemaQhtriSemanticLoopError("spinor_sheet must be -1 or +1")
    _require_hex64(receipt.get("cp1_poincare_adapter_commitment"), "cp1_poincare_adapter_commitment")
    _require_hex64(receipt.get("holonomy_audit_commitment"), "holonomy_audit_commitment")
    _verify_seal(receipt, "anchor_receipt_sha256")


def build_semantic_path_receipt(
    anchors: Sequence[Mapping[str, Any]],
    *,
    ordered_relation_ids: Sequence[str],
    ordered_kaku_candidate_ids: Sequence[str],
    ordered_radical_candidate_ids: Sequence[str],
    ordered_operator_candidate_ids: Sequence[str],
    gremlin_isomorphism_ids: Sequence[str],
) -> dict[str, Any]:
    if not anchors:
        raise NoemaQhtriSemanticLoopError("semantic path requires at least one anchor")
    for anchor in anchors:
        validate_projective_anchor_receipt(anchor)
    bank_hashes = {anchor["bank_manifest_sha256"] for anchor in anchors}
    if len(bank_hashes) != 1:
        raise NoemaQhtriSemanticLoopError("semantic path anchors must share one GREMLIN bank generation")
    relation_ids = tuple(_require_text(value, "relation_id") for value in ordered_relation_ids)
    if len(relation_ids) != len(anchors) - 1:
        raise NoemaQhtriSemanticLoopError("semantic path relation cardinality mismatch")
    kaku_ids = tuple(_require_text(value, "kaku_candidate_id") for value in ordered_kaku_candidate_ids)
    radical_ids = tuple(_require_text(value, "radical_candidate_id") for value in ordered_radical_candidate_ids)
    operator_ids = tuple(_require_text(value, "operator_candidate_id") for value in ordered_operator_candidate_ids)
    if not kaku_ids or not radical_ids or not operator_ids:
        raise NoemaQhtriSemanticLoopError("semantic path requires KAKU, RADICAL and OPERATORS lineage")
    iso_ids = _require_bank_subset(gremlin_isomorphism_ids)
    meaning_body = {
        "ordered_anchor_commitments": [anchor["anchor_receipt_sha256"] for anchor in anchors],
        "ordered_relation_ids": list(relation_ids),
        "ordered_kaku_candidate_ids": list(kaku_ids),
        "ordered_radical_candidate_ids": list(radical_ids),
        "ordered_operator_candidate_ids": list(operator_ids),
        "gremlin_isomorphism_ids": list(iso_ids),
    }
    body = {
        "schema": SEMANTIC_PATH_SCHEMA,
        "bank_manifest_sha256": next(iter(bank_hashes)),
        **meaning_body,
        "meaning_commitment": _sha256(meaning_body),
    }
    return _seal(body, "semantic_path_receipt_sha256")


def validate_semantic_path_receipt(receipt: Mapping[str, Any]) -> None:
    if receipt.get("schema") != SEMANTIC_PATH_SCHEMA:
        raise NoemaQhtriSemanticLoopError("invalid semantic path schema")
    _require_hex64(receipt.get("bank_manifest_sha256"), "bank_manifest_sha256")
    anchors = tuple(receipt.get("ordered_anchor_commitments", ()))
    if not anchors:
        raise NoemaQhtriSemanticLoopError("semantic path requires anchor commitments")
    for value in anchors:
        _require_hex64(value, "anchor_receipt_sha256")
    relations = tuple(receipt.get("ordered_relation_ids", ()))
    if len(relations) != len(anchors) - 1:
        raise NoemaQhtriSemanticLoopError("semantic path relation cardinality mismatch")
    for value in relations:
        _require_text(value, "relation_id")
    for key in (
        "ordered_kaku_candidate_ids",
        "ordered_radical_candidate_ids",
        "ordered_operator_candidate_ids",
    ):
        values = tuple(receipt.get(key, ()))
        if not values:
            raise NoemaQhtriSemanticLoopError(f"semantic path requires {key}")
        for value in values:
            _require_text(value, key)
    iso_ids = _require_bank_subset(tuple(receipt.get("gremlin_isomorphism_ids", ())))
    meaning_body = {
        "ordered_anchor_commitments": list(anchors),
        "ordered_relation_ids": list(relations),
        "ordered_kaku_candidate_ids": list(receipt["ordered_kaku_candidate_ids"]),
        "ordered_radical_candidate_ids": list(receipt["ordered_radical_candidate_ids"]),
        "ordered_operator_candidate_ids": list(receipt["ordered_operator_candidate_ids"]),
        "gremlin_isomorphism_ids": list(iso_ids),
    }
    if receipt.get("meaning_commitment") != _sha256(meaning_body):
        raise NoemaQhtriSemanticLoopError("meaning commitment mismatch")
    _verify_seal(receipt, "semantic_path_receipt_sha256")


def build_state_crystal_receipt(
    semantic_path_receipt: Mapping[str, Any],
    *,
    state_object_id: str,
    pnfs_object_id: str,
    generation: int,
    memory_epoch: int,
    checkpoint_commitment: str,
    identity_layer_mutation: bool = False,
    identity_authority_ref: str | None = None,
) -> dict[str, Any]:
    validate_semantic_path_receipt(semantic_path_receipt)
    if not isinstance(identity_layer_mutation, bool):
        raise NoemaQhtriSemanticLoopError("identity_layer_mutation must be boolean")
    authority_ref = ""
    if identity_layer_mutation:
        authority_ref = _require_text(identity_authority_ref, "identity_authority_ref")
    body = {
        "schema": STATE_CRYSTAL_SCHEMA,
        "bank_manifest_sha256": semantic_path_receipt["bank_manifest_sha256"],
        "semantic_path_receipt_sha256": semantic_path_receipt["semantic_path_receipt_sha256"],
        "state_object_id": _require_text(state_object_id, "state_object_id"),
        "pnfs_object_id": _require_text(pnfs_object_id, "pnfs_object_id"),
        "generation": _require_nonnegative_int(generation, "generation"),
        "memory_epoch": _require_nonnegative_int(memory_epoch, "memory_epoch"),
        "checkpoint_commitment": _require_hex64(checkpoint_commitment, "checkpoint_commitment"),
        "append_only": True,
        "identity_layer_mutation": identity_layer_mutation,
        "identity_authority_ref": authority_ref,
    }
    return _seal(body, "state_crystal_receipt_sha256")


def validate_state_crystal_receipt(receipt: Mapping[str, Any]) -> None:
    if receipt.get("schema") != STATE_CRYSTAL_SCHEMA:
        raise NoemaQhtriSemanticLoopError("invalid state crystal schema")
    _require_hex64(receipt.get("bank_manifest_sha256"), "bank_manifest_sha256")
    _require_hex64(receipt.get("semantic_path_receipt_sha256"), "semantic_path_receipt_sha256")
    _require_text(receipt.get("state_object_id"), "state_object_id")
    _require_text(receipt.get("pnfs_object_id"), "pnfs_object_id")
    _require_nonnegative_int(receipt.get("generation"), "generation")
    _require_nonnegative_int(receipt.get("memory_epoch"), "memory_epoch")
    _require_hex64(receipt.get("checkpoint_commitment"), "checkpoint_commitment")
    if receipt.get("append_only") is not True:
        raise NoemaQhtriSemanticLoopError("state crystal must be append-only")
    mutation = receipt.get("identity_layer_mutation")
    if not isinstance(mutation, bool):
        raise NoemaQhtriSemanticLoopError("identity_layer_mutation must be boolean")
    if mutation:
        _require_text(receipt.get("identity_authority_ref"), "identity_authority_ref")
    elif receipt.get("identity_authority_ref", "") != "":
        raise NoemaQhtriSemanticLoopError("identity authority must be empty outside an identity mutation")
    _verify_seal(receipt, "state_crystal_receipt_sha256")


def build_feedback_candidate_receipt(
    state_crystal_receipt: Mapping[str, Any],
    *,
    hermitian_operator_commitment: str,
    pncap_admission_token: str,
    qhtri_target_ref: str,
) -> dict[str, Any]:
    validate_state_crystal_receipt(state_crystal_receipt)
    body = {
        "schema": FEEDBACK_SCHEMA,
        "bank_manifest_sha256": state_crystal_receipt["bank_manifest_sha256"],
        "state_crystal_receipt_sha256": state_crystal_receipt["state_crystal_receipt_sha256"],
        "hermitian_operator_commitment": _require_hex64(
            hermitian_operator_commitment, "hermitian_operator_commitment"
        ),
        "pncap_admission_token": _require_text(pncap_admission_token, "pncap_admission_token"),
        "effect_policy": EFFECT_POLICY,
        "qhtri_target_ref": _require_text(qhtri_target_ref, "qhtri_target_ref"),
        "execution_admitted": False,
        "production_runtime_write": False,
    }
    return _seal(body, "feedback_receipt_sha256")


def validate_feedback_candidate_receipt(receipt: Mapping[str, Any]) -> None:
    if receipt.get("schema") != FEEDBACK_SCHEMA:
        raise NoemaQhtriSemanticLoopError("invalid feedback candidate schema")
    _require_hex64(receipt.get("bank_manifest_sha256"), "bank_manifest_sha256")
    _require_hex64(receipt.get("state_crystal_receipt_sha256"), "state_crystal_receipt_sha256")
    _require_hex64(receipt.get("hermitian_operator_commitment"), "hermitian_operator_commitment")
    _require_text(receipt.get("pncap_admission_token"), "pncap_admission_token")
    if receipt.get("effect_policy") != EFFECT_POLICY:
        raise NoemaQhtriSemanticLoopError("feedback effect policy mismatch")
    _require_text(receipt.get("qhtri_target_ref"), "qhtri_target_ref")
    if receipt.get("execution_admitted") is not False:
        raise NoemaQhtriSemanticLoopError("candidate receipt crossed execution-admission boundary")
    if receipt.get("production_runtime_write") is not False:
        raise NoemaQhtriSemanticLoopError("candidate receipt crossed production-write boundary")
    _verify_seal(receipt, "feedback_receipt_sha256")


def build_loop_receipt(
    *,
    bifurcation_receipt: Mapping[str, Any],
    anchor_receipt: Mapping[str, Any],
    semantic_path_receipt: Mapping[str, Any],
    state_crystal_receipt: Mapping[str, Any],
    feedback_receipt: Mapping[str, Any],
    require_full_bank: bool = True,
) -> dict[str, Any]:
    validate_bifurcation_receipt(bifurcation_receipt)
    validate_projective_anchor_receipt(anchor_receipt)
    validate_semantic_path_receipt(semantic_path_receipt)
    validate_state_crystal_receipt(state_crystal_receipt)
    validate_feedback_candidate_receipt(feedback_receipt)

    if anchor_receipt["bifurcation_receipt_sha256"] != bifurcation_receipt["bifurcation_receipt_sha256"]:
        raise NoemaQhtriSemanticLoopError("anchor parent mismatch")
    if anchor_receipt["anchor_receipt_sha256"] not in semantic_path_receipt["ordered_anchor_commitments"]:
        raise NoemaQhtriSemanticLoopError("semantic path does not include the supplied anchor")
    if state_crystal_receipt["semantic_path_receipt_sha256"] != semantic_path_receipt["semantic_path_receipt_sha256"]:
        raise NoemaQhtriSemanticLoopError("state crystal parent mismatch")
    if feedback_receipt["state_crystal_receipt_sha256"] != state_crystal_receipt["state_crystal_receipt_sha256"]:
        raise NoemaQhtriSemanticLoopError("feedback parent mismatch")

    bank_hashes = {
        bifurcation_receipt["bank_manifest_sha256"],
        anchor_receipt["bank_manifest_sha256"],
        semantic_path_receipt["bank_manifest_sha256"],
        state_crystal_receipt["bank_manifest_sha256"],
        feedback_receipt["bank_manifest_sha256"],
    }
    if len(bank_hashes) != 1:
        raise NoemaQhtriSemanticLoopError("loop stages must share one GREMLIN bank generation")

    iso_ids = tuple(semantic_path_receipt["gremlin_isomorphism_ids"])
    if require_full_bank and iso_ids != FULL_BANK_ISOMORPHISM_IDS:
        raise NoemaQhtriSemanticLoopError("full loop requires all GREMLIN bank entries in canonical order")

    body = {
        "schema": LOOP_SCHEMA,
        "bank_manifest_sha256": next(iter(bank_hashes)),
        "ordered_isomorphism_ids": list(iso_ids),
        "full_bank": bool(require_full_bank),
        "bifurcation_receipt_sha256": bifurcation_receipt["bifurcation_receipt_sha256"],
        "anchor_receipt_sha256": anchor_receipt["anchor_receipt_sha256"],
        "semantic_path_receipt_sha256": semantic_path_receipt["semantic_path_receipt_sha256"],
        "state_crystal_receipt_sha256": state_crystal_receipt["state_crystal_receipt_sha256"],
        "feedback_receipt_sha256": feedback_receipt["feedback_receipt_sha256"],
        "runtime_execution_authority": False,
        "canon_write_authority": False,
        "epistemic": "CHYBA",
    }
    return _seal(body, "loop_receipt_sha256")


def validate_loop_receipt(
    receipt: Mapping[str, Any],
    *,
    bifurcation_receipt: Mapping[str, Any],
    anchor_receipt: Mapping[str, Any],
    semantic_path_receipt: Mapping[str, Any],
    state_crystal_receipt: Mapping[str, Any],
    feedback_receipt: Mapping[str, Any],
) -> None:
    if receipt.get("schema") != LOOP_SCHEMA:
        raise NoemaQhtriSemanticLoopError("invalid loop schema")
    expected = build_loop_receipt(
        bifurcation_receipt=bifurcation_receipt,
        anchor_receipt=anchor_receipt,
        semantic_path_receipt=semantic_path_receipt,
        state_crystal_receipt=state_crystal_receipt,
        feedback_receipt=feedback_receipt,
        require_full_bank=bool(receipt.get("full_bank")),
    )
    if dict(receipt) != expected:
        raise NoemaQhtriSemanticLoopError("loop receipt does not match deterministic reconstruction")
